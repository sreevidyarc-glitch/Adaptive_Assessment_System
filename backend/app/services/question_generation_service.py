import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.course import Course, CourseObjective, CourseMaterialChunk
from app.models.question import Trait, Question, Rubric, ModelAnswer
from app.services.question_allocation_service import (
    allocate_objectives_largest_remainder,
    allocate_traits_quota_deficits
)
from app.services.question_validation_service import validate_all
from app.services.gemini_service import gemini_service

logger = logging.getLogger("adaptive_assessment.question_generation")

def generate_course_question_set(
    course_id: str,
    total_questions: int,
    db: Session,
    objective_weights: Optional[Dict[str, float]] = None,
    trait_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Executes Stages 3 & 4 of Integrated Algorithm:
    1. Allocates N questions across objectives using the largest remainder method.
    2. Allocates questions across traits using remaining quota deficits.
    3. Retrieves relevant course chunks for each objective.
    4. Calls LLM service (Gemini) to generate Question, Rubric, Model Answer, Hints.
    5. Validates: Schema, Hint leakage, Rubric sanity, Duplicate questions.
    6. Retries up to 3 times on validation failure.
    7. Stores questions in database pending faculty approval.
    """
    # 1. Fetch Course, Objectives, Traits
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Course not found.")

    objectives = db.query(CourseObjective).filter(CourseObjective.course_id == course_id).all()
    if not objectives:
        raise ValueError("No learning objectives found for this course.")

    traits = db.query(Trait).all()
    if not traits:
        # Fallback default traits if none exist
        traits = [
            Trait(code="TR_CONCEPT", name="Conceptual Clarity", description="Theoretical grounding"),
            Trait(code="TR_PROBLEM", name="Problem Solving", description="Implementation of algorithms"),
            Trait(code="TR_ANALYSIS", name="Analytical Rigor", description="Complexity analysis & proofs")
        ]
        for t in traits:
            db.add(t)
        db.commit()

    # Apply optional custom weights
    objectives_data = [
        {
            "id": o.id,
            "code": o.code,
            "description": o.description,
            "weight": objective_weights.get(o.id, o.weight) if objective_weights else o.weight
        }
        for o in objectives
    ]
    obj_meta_map = {o["id"]: o for o in objectives_data}

    traits_data = [
        {
            "id": t.id,
            "code": t.code,
            "name": t.name,
            "weight": trait_weights.get(t.id, 1.0) if trait_weights else 1.0
        }
        for t in traits
    ]

    # 2. Largest Remainder Method Allocation across Objectives
    allocated_objectives = allocate_objectives_largest_remainder(total_questions, objectives_data)

    # 3. Quota Deficits Allocation across Traits
    planned_questions = allocate_traits_quota_deficits(
        allocated_objectives=allocated_objectives,
        traits=traits_data,
        objective_metadata=obj_meta_map
    )

    # 4. Fetch existing question prompts in this course (for duplicate detection)
    existing_q_records = db.query(Question.prompt).filter(Question.course_id == course_id).all()
    existing_prompts: List[str] = [q[0] for q in existing_q_records]

    generated_questions = []
    unresolved_failures = 0

    # 5. Generation and Validation Loop (with 3-Retry Backoff)
    for q_idx, planned in enumerate(planned_questions):
        obj_id = planned["objective_id"]
        trait_id = planned["trait_id"]

        # Retrieve relevant chunks mapped to this objective
        chunks = db.query(CourseMaterialChunk.content).filter(
            CourseMaterialChunk.course_id == course_id,
            CourseMaterialChunk.mapped_objective_id == obj_id
        ).limit(4).all()
        context_chunks = [c[0] for c in chunks]

        candidate = None
        is_valid = False
        failures = []
        retries_used = 0
        retry_feedback = None

        # Up to 3 Retries
        for attempt in range(1, 4):
            retries_used = attempt
            candidate = gemini_service.generate_assessment_question(
                objective_code=planned["objective_code"],
                objective_description=planned["objective_description"],
                trait_name=planned["trait_name"],
                context_chunks=context_chunks,
                retry_feedback=retry_feedback,
                variation_index=q_idx + attempt
            )

            is_valid, failures = validate_all(candidate, existing_prompts)
            if is_valid:
                break
            else:
                retry_feedback = "; ".join(failures)
                logger.warning(
                    f"Validation attempt {attempt}/3 failed for {planned['objective_code']} ({planned['trait_name']}): {retry_feedback}"
                )

        validation_status = "PASSED" if is_valid else "UNRESOLVED_FAILURE"
        if not is_valid:
            unresolved_failures += 1

        # Persist question, rubric, and model answer in DB
        db_question = Question(
            course_id=course_id,
            objective_id=obj_id,
            trait_id=trait_id,
            prompt=candidate["question"],
            hint1=candidate.get("hint1", ""),
            hint2=candidate.get("hint2", ""),
            is_approved=False,  # Requires Faculty Review
            is_published=False, # Kept strictly secret from students until approved
            generation_retries=retries_used,
            validation_status=validation_status,
            validation_notes="; ".join(failures) if failures else "All 4 validations passed."
        )
        db.add(db_question)
        db.flush()

        # Rubric (Privileged)
        rubric_data = candidate["rubric"]
        db_rubric = Rubric(
            question_id=db_question.id,
            total_points=rubric_data.get("total_points", 10.0),
            criteria=rubric_data.get("criteria", [])
        )
        db.add(db_rubric)

        # Model Answer (Privileged)
        db_model_answer = ModelAnswer(
            question_id=db_question.id,
            content=candidate["model_answer"],
            explanation=candidate.get("explanation", f"Aligned with objective {planned['objective_code']} and trait {planned['trait_name']}.")
        )
        db.add(db_model_answer)

        db.commit()
        db.refresh(db_question)

        # Track prompt to avoid duplicates within the same batch
        existing_prompts.append(db_question.prompt)

        generated_questions.append({
            "id": db_question.id,
            "objective_code": planned["objective_code"],
            "trait_name": planned["trait_name"],
            "prompt": db_question.prompt,
            "hint1": db_question.hint1,
            "hint2": db_question.hint2,
            "generation_retries": db_question.generation_retries,
            "validation_status": db_question.validation_status,
            "validation_notes": db_question.validation_notes,
            "rubric": {
                "id": db_rubric.id,
                "total_points": db_rubric.total_points,
                "criteria": db_rubric.criteria
            },
            "model_answer": {
                "id": db_model_answer.id,
                "content": db_model_answer.content,
                "explanation": db_model_answer.explanation
            }
        })

    # Allocation summaries
    allocations_summary = []
    for obj_id, count in allocated_objectives.items():
        obj = obj_meta_map.get(obj_id, {})
        allocations_summary.append({
            "objective_id": obj_id,
            "objective_code": obj.get("code", "CO"),
            "question_count": count
        })

    return {
        "course_id": course_id,
        "total_requested": total_questions,
        "total_generated": len(generated_questions),
        "unresolved_failures_count": unresolved_failures,
        "allocations": allocations_summary,
        "questions": generated_questions
    }
