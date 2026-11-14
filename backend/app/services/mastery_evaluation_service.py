import re
import math
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.course import Course, CourseObjective, CourseEnrollment
from app.models.question import Question, Rubric, ModelAnswer, Trait
from app.models.assessment import AssessmentSession, StudentResponse, MasteryScore, AssessmentStatusEnum
from app.services.gemini_service import GeminiService

def utcnow():
    return datetime.now(timezone.utc)

def calculate_rubric_fraction(earned_points: float, total_points: float) -> float:
    """
    Calculates rubric achievement fraction:
    f_i = earned rubric points / total rubric points
    
    Enforces invariants:
    - Denominator total_points > 0
    - f_i is clamped to [0.0, 1.0]
    """
    if total_points <= 0:
        raise ValueError("Rubric denominator (total_points) must be greater than zero.")
    
    fraction = earned_points / total_points
    return max(0.0, min(1.0, round(fraction, 6)))

def calculate_objective_trait_mastery(evidence_list: List[Tuple[float, float]]) -> float:
    """
    Calculates Objective-Trait mastery:
    M_o,t = (1 + sum(w_i * f_i)) / (2 + sum(w_i))
    
    Acts as Laplace/Bayesian smoothing with prior 0.5 at zero evidence.
    Enforces invariants:
    - All evidence weights w_i >= 0
    - Denominator (2 + sum(w_i)) > 0
    - Strictly bounded in (0.0, 1.0)
    """
    if not evidence_list:
        return 0.5  # Prior at zero evidence

    sum_w = 0.0
    sum_wf = 0.0

    for weight, fraction in evidence_list:
        if weight < 0:
            raise ValueError(f"Evidence weight w_i must be non-negative, got {weight}")
        sum_w += weight
        clamped_f = max(0.0, min(1.0, fraction))
        sum_wf += weight * clamped_f

    denominator = 2.0 + sum_w
    if denominator <= 0:
        raise ValueError("Mastery denominator must be positive.")

    mastery = (1.0 + sum_wf) / denominator
    return max(0.0, min(1.0, round(mastery, 6)))

def calculate_learning_gap(
    mastery_value: float,
    objective_weight: float = 1.0,
    tau: float = 0.75
) -> Tuple[float, str]:
    """
    Calculates Learning Gap:
    G_o,t = max(0.0, (tau - M_o,t) * w_o)
    
    Classification:
    IF M_o,t < 0.3 THEN Recommend foundational learning
    ELSE Recommend reinforcement learning
    """
    clamped_m = max(0.0, min(1.0, mastery_value))
    raw_gap = (tau - clamped_m) * max(0.0, objective_weight)
    gap_score = max(0.0, round(raw_gap, 6))

    if clamped_m < 0.30:
        recommendation_type = "FOUNDATIONAL"
    else:
        recommendation_type = "REINFORCEMENT"

    return gap_score, recommendation_type

def evaluate_response_lexical_fallback(
    student_response: str,
    rubric_criteria: List[Dict[str, Any]],
    total_rubric_points: float,
    model_answer: Optional[str] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Deterministic rubric evaluation fallback when external LLM is offline or not configured.
    Evaluates student response against criteria concepts and model answer key terms.
    """
    if not student_response or not student_response.strip():
        return 0.0, {"breakdown": [], "notes": "Empty response submitted."}

    norm_response = student_response.lower()
    words = set(re.findall(r'\b[a-z]{3,}\b', norm_response))
    total_earned = 0.0
    criterion_results = []

    for idx, crit in enumerate(rubric_criteria or []):
        crit_desc = crit.get("criterion", "").lower()
        crit_pts = float(crit.get("max_points", 2.0))
        crit_words = set(re.findall(r'\b[a-z]{3,}\b', crit_desc))
        
        # Calculate keyword match ratio
        if crit_words:
            overlap = words.intersection(crit_words)
            ratio = min(1.0, len(overlap) / max(1, len(crit_words) * 0.4))
        else:
            ratio = 0.5  # default baseline if criterion has no keywords
        
        # Consider length/thoroughness
        length_factor = min(1.0, len(student_response.split()) / 25.0)
        score = round(crit_pts * (0.4 * ratio + 0.6 * length_factor), 2)
        score = min(score, crit_pts)
        total_earned += score

        criterion_results.append({
            "criterion_index": idx,
            "criterion": crit.get("criterion", ""),
            "max_points": crit_pts,
            "earned_points": score
        })

    # Clamp total earned to total_rubric_points
    total_earned = min(total_earned, total_rubric_points)
    return round(total_earned, 2), {"breakdown": criterion_results, "evaluator": "lexical_fallback"}

class MasteryEvaluationService:
    @staticmethod
    def evaluate_response(
        question: Question,
        student_response: str,
        hints_used: int = 0
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Evaluates student response against approved server-side rubric.
        NEVER expose the rubric or model answer in returned payload for students.
        """
        rubric = question.rubric
        if not rubric or rubric.total_points <= 0:
            total_pts = 10.0
            criteria = [{"criterion": "General correctness and clarity", "max_points": 10.0}]
        else:
            total_pts = rubric.total_points
            criteria = rubric.criteria if isinstance(rubric.criteria, list) else []

        model_answer_text = question.model_answer.content if question.model_answer else None

        # Attempt LLM evaluation if configured
        gemini = GeminiService()
        earned_points = 0.0
        details = {}

        if gemini.is_available() and student_response.strip():
            eval_res = gemini.evaluate_student_response(
                question_prompt=question.prompt,
                rubric_criteria=criteria,
                total_rubric_points=total_pts,
                model_answer=model_answer_text,
                student_response=student_response,
                hints_used=hints_used
            )
            if eval_res and "earned_points" in eval_res:
                earned_points = float(eval_res["earned_points"])
                details = eval_res.get("details", {})
            else:
                earned_points, details = evaluate_response_lexical_fallback(
                    student_response, criteria, total_pts, model_answer_text
                )
        else:
            earned_points, details = evaluate_response_lexical_fallback(
                student_response, criteria, total_pts, model_answer_text
            )

        # Apply minor hint penalty if hints were used (e.g. 5% reduction per hint, max 10%)
        if hints_used > 0:
            penalty_ratio = min(0.10, hints_used * 0.05)
            earned_points = max(0.0, earned_points * (1.0 - penalty_ratio))

        earned_points = min(earned_points, total_pts)
        f_i = calculate_rubric_fraction(earned_points, total_pts)
        return earned_points, f_i, details

    @staticmethod
    def process_submission(
        db: Session,
        session_id: str,
        student_id: str,
        submissions: List[Dict[str, Any]],
        tau: float = 0.75
    ) -> Dict[str, Any]:
        """
        Processes an assessment session submission:
        1. Evaluates responses against server-side rubrics.
        2. Calculates f_i = earned rubric points / total rubric points.
        3. Updates StudentResponse records.
        4. Calculates M_o,t = (1 + sum(w_i * f_i)) / (2 + sum(w_i)) for each objective-trait pair.
        5. Computes G_o,t = max(0.0, (tau - M_o,t) * w_o) and assigns FOUNDATIONAL/REINFORCEMENT.
        6. Persists separate MasteryScore records for every (o, t).
        """
        session = db.query(AssessmentSession).filter(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == student_id
        ).first()

        if not session:
            raise ValueError("Assessment session not found or does not belong to student.")

        if session.status == AssessmentStatusEnum.COMPLETED:
            raise ValueError("Assessment session has already been completed.")

        course_id = session.course_id
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Course not found.")

        # Map submissions by question_id
        sub_map = {s["question_id"]: s for s in submissions}
        question_ids = list(sub_map.keys())

        questions = db.query(Question).filter(
            Question.id.in_(question_ids),
            Question.course_id == course_id,
            Question.is_published == True
        ).all()

        # Track evidence by (objective_id, trait_id)
        # evidence_store[(o_id, t_id)] = list of (weight_i, f_i)
        evidence_store: Dict[Tuple[str, Optional[str]], List[Tuple[float, float]]] = {}
        total_session_earned = 0.0
        total_session_possible = 0.0
        evaluated_results = []

        for q in questions:
            user_sub = sub_map.get(q.id, {})
            resp_text = user_sub.get("response_text", "")
            hints_used = int(user_sub.get("hints_used", 0))

            earned_pts, f_i, eval_meta = MasteryEvaluationService.evaluate_response(
                question=q,
                student_response=resp_text,
                hints_used=hints_used
            )

            # Record or update StudentResponse
            existing_resp = db.query(StudentResponse).filter(
                StudentResponse.session_id == session.id,
                StudentResponse.question_id == q.id
            ).first()

            if existing_resp:
                existing_resp.response_text = resp_text
                existing_resp.hints_used = hints_used
                existing_resp.earned_points = earned_pts
                existing_resp.evaluated_at = utcnow()
            else:
                db_resp = StudentResponse(
                    session_id=session.id,
                    question_id=q.id,
                    response_text=resp_text,
                    hints_used=hints_used,
                    earned_points=earned_pts,
                    evaluated_at=utcnow()
                )
                db.add(db_resp)

            total_pts = q.rubric.total_points if (q.rubric and q.rubric.total_points > 0) else 10.0
            total_session_earned += earned_pts
            total_session_possible += total_pts

            # Evidence weight w_i: defaults to 1.0 or normalized by question total points
            w_i = 1.0
            pair_key = (q.objective_id, q.trait_id)
            if pair_key not in evidence_store:
                evidence_store[pair_key] = []
            evidence_store[pair_key].append((w_i, f_i))

            # Student result view: DO NOT leak rubric details or model answer
            evaluated_results.append({
                "question_id": q.id,
                "earned_points": round(earned_pts, 2),
                "total_points": round(total_pts, 2),
                "fraction_achieved": round(f_i, 4),
                "hints_used": hints_used
            })

        # Calculate and update MasteryScore for each (o, t)
        all_objectives = db.query(CourseObjective).filter(CourseObjective.course_id == course_id).all()
        obj_map = {o.id: o for o in all_objectives}

        # Include prior assessment responses for this student in this course to maintain rolling cumulative mastery
        for (o_id, t_id), new_evidence in evidence_store.items():
            # Query historical responses for this student, course, and (o, t)
            historical_responses = db.query(StudentResponse).join(Question).join(AssessmentSession).filter(
                AssessmentSession.student_id == student_id,
                AssessmentSession.course_id == course_id,
                AssessmentSession.id != session.id,
                Question.objective_id == o_id,
                Question.trait_id == t_id
            ).all()

            combined_evidence = list(new_evidence)
            for hr in historical_responses:
                hr_pts = hr.earned_points or 0.0
                hq = db.query(Question).filter(Question.id == hr.question_id).first()
                total_pts = hq.rubric.total_points if (hq and hq.rubric and hq.rubric.total_points > 0) else 10.0
                hr_f = calculate_rubric_fraction(hr_pts, total_pts)
                combined_evidence.append((1.0, hr_f))

            m_val = calculate_objective_trait_mastery(combined_evidence)
            obj = obj_map.get(o_id)
            w_o = obj.weight if obj and obj.weight is not None else 1.0
            gap_val, rec_type = calculate_learning_gap(m_val, objective_weight=w_o, tau=tau)

            # Upsert MasteryScore
            existing_score = db.query(MasteryScore).filter(
                MasteryScore.student_id == student_id,
                MasteryScore.course_id == course_id,
                MasteryScore.objective_id == o_id,
                MasteryScore.trait_id == t_id
            ).first()

            if existing_score:
                existing_score.mastery_value = m_val
                existing_score.gap_score = gap_val
                existing_score.recommendation_type = rec_type
                existing_score.updated_at = utcnow()
            else:
                db_score = MasteryScore(
                    student_id=student_id,
                    course_id=course_id,
                    objective_id=o_id,
                    trait_id=t_id,
                    mastery_value=m_val,
                    gap_score=gap_val,
                    recommendation_type=rec_type,
                    updated_at=utcnow()
                )
                db.add(db_score)

        # Finalize Assessment Session
        session.status = AssessmentStatusEnum.COMPLETED
        session.completed_at = utcnow()
        session.post_score = round(total_session_earned / total_session_possible, 4) if total_session_possible > 0 else 0.0

        db.commit()

        return {
            "session_id": session.id,
            "course_id": course_id,
            "status": session.status.value,
            "total_questions": len(questions),
            "earned_points": round(total_session_earned, 2),
            "total_possible_points": round(total_session_possible, 2),
            "overall_percentage": round((total_session_earned / total_session_possible) * 100, 2) if total_session_possible > 0 else 0.0,
            "results": evaluated_results
        }

    @staticmethod
    def get_student_mastery_matrix(db: Session, student_id: str, course_id: str, tau: float = 0.75) -> Dict[str, Any]:
        """
        Generates student's personal |O| x |T| mastery matrix.
        Students can view ONLY their own matrix.
        """
        objectives = db.query(CourseObjective).filter(CourseObjective.course_id == course_id).all()
        traits = db.query(Trait).all()

        # Fetch student's mastery records for this course
        records = db.query(MasteryScore).filter(
            MasteryScore.student_id == student_id,
            MasteryScore.course_id == course_id
        ).all()

        record_map = {(r.objective_id, r.trait_id): r for r in records}

        matrix_rows = []
        all_masteries = []
        gaps_list = []

        for obj in objectives:
            cells = []
            for tr in traits:
                rec = record_map.get((obj.id, tr.id))
                if rec:
                    m_val = round(rec.mastery_value, 4)
                    g_val = round(rec.gap_score, 4)
                    rec_type = rec.recommendation_type
                else:
                    # Unattempted prior M = 0.5
                    m_val = 0.50
                    g_val, rec_type = calculate_learning_gap(m_val, objective_weight=obj.weight, tau=tau)
                    g_val = round(g_val, 4)

                all_masteries.append(m_val)
                cell_data = {
                    "trait_id": tr.id,
                    "trait_code": tr.code,
                    "trait_name": tr.name,
                    "mastery_value": m_val,
                    "gap_score": g_val,
                    "recommendation_type": rec_type
                }
                cells.append(cell_data)

                if g_val > 0:
                    gaps_list.append({
                        "objective_id": obj.id,
                        "objective_code": obj.code,
                        "objective_description": obj.description,
                        "trait_code": tr.code,
                        "trait_name": tr.name,
                        "mastery_value": m_val,
                        "gap_score": g_val,
                        "recommendation_type": rec_type
                    })

            matrix_rows.append({
                "objective_id": obj.id,
                "objective_code": obj.code,
                "objective_description": obj.description,
                "priority_weight": obj.weight,
                "traits": cells
            })

        # Rank learning gaps in descending order
        gaps_list.sort(key=lambda x: x["gap_score"], reverse=True)

        avg_mastery = round(sum(all_masteries) / len(all_masteries), 4) if all_masteries else 0.5

        return {
            "course_id": course_id,
            "overall_average_mastery": avg_mastery,
            "tau_threshold": tau,
            "matrix": matrix_rows,
            "ranked_learning_gaps": gaps_list
        }

    @staticmethod
    def get_class_mastery_matrix(db: Session, course_id: str, tau: float = 0.75) -> Dict[str, Any]:
        """
        Generates class-level aggregate mastery matrix across all enrolled students.
        Accessible only by authorized faculty assigned to the course.
        Protects student anonymity through aggregation.
        """
        enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.course_id == course_id).all()
        student_ids = [e.student_id for e in enrollments]
        total_students = len(student_ids)

        objectives = db.query(CourseObjective).filter(CourseObjective.course_id == course_id).all()
        traits = db.query(Trait).all()

        if total_students == 0:
            return {
                "course_id": course_id,
                "total_enrolled_students": 0,
                "matrix": [],
                "summary": "No students currently enrolled."
            }

        matrix_rows = []
        for obj in objectives:
            trait_summaries = []
            for tr in traits:
                scores = db.query(MasteryScore).filter(
                    MasteryScore.course_id == course_id,
                    MasteryScore.student_id.in_(student_ids),
                    MasteryScore.objective_id == obj.id,
                    MasteryScore.trait_id == tr.id
                ).all()

                if scores:
                    values = [s.mastery_value for s in scores]
                    mean_val = round(sum(values) / len(values), 4)
                    min_val = round(min(values), 4)
                    max_val = round(max(values), 4)
                    gap_count = sum(1 for s in scores if s.gap_score > 0)
                    foundational_count = sum(1 for s in scores if s.recommendation_type == "FOUNDATIONAL")
                    reinforcement_count = sum(1 for s in scores if s.recommendation_type == "REINFORCEMENT")
                else:
                    mean_val = 0.50
                    min_val = 0.50
                    max_val = 0.50
                    gap_count = 0
                    foundational_count = 0
                    reinforcement_count = 0

                trait_summaries.append({
                    "trait_id": tr.id,
                    "trait_code": tr.code,
                    "trait_name": tr.name,
                    "mean_mastery": mean_val,
                    "min_mastery": min_val,
                    "max_mastery": max_val,
                    "students_with_gaps": gap_count,
                    "foundational_remedial_count": foundational_count,
                    "reinforcement_count": reinforcement_count
                })

            matrix_rows.append({
                "objective_id": obj.id,
                "objective_code": obj.code,
                "objective_description": obj.description,
                "priority_weight": obj.weight,
                "traits": trait_summaries
            })

        return {
            "course_id": course_id,
            "total_enrolled_students": total_students,
            "tau_threshold": tau,
            "matrix": matrix_rows
        }
