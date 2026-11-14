import uuid
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.course import Course, CourseObjective, CourseEnrollment, CourseMaterialChunk
from app.models.question import Question, Rubric, ModelAnswer, Trait
from app.models.assessment import (
    AssessmentSession,
    StudentResponse,
    MasteryScore,
    AssessmentStatusEnum,
    RemedialPack
)
from app.services.mastery_evaluation_service import (
    calculate_rubric_fraction,
    calculate_objective_trait_mastery,
    calculate_learning_gap,
    MasteryEvaluationService
)

def utcnow():
    return datetime.now(timezone.utc)

def calculate_normalized_learning_gain(pre_score: float, post_score: float) -> Tuple[float, str, str]:
    """
    Calculates Hake's Normalized Learning Gain:
    g = (Post - Pre) / (1 - Pre)
    
    Enforces strict mathematical invariants:
    - Pre and Post must be normalized in [0.0, 1.0].
    - If Pre == 1.0, normalized gain is mathematically undefined -> raises ValueError.
    - Categorizes gain: High (>= 0.70), Medium (0.30 <= g < 0.70), Low (< 0.30).
    """
    if pre_score < 0.0 or pre_score > 1.0 or post_score < 0.0 or post_score > 1.0:
        raise ValueError(f"Pre ({pre_score}) and Post ({post_score}) scores must be normalized in the range [0.0, 1.0].")

    if abs(pre_score - 1.0) < 1e-9:
        raise ValueError("Normalized gain is undefined when Pre = 1.")

    g = (post_score - pre_score) / (1.0 - pre_score)
    g_rounded = round(g, 4)

    if g_rounded >= 0.70:
        category = "HIGH"
        interpretation = "High Learning Gain: Demonstrates outstanding conceptual mastery and gap elimination."
    elif g_rounded >= 0.30:
        category = "MEDIUM"
        interpretation = "Medium Learning Gain: Measurable academic progression with effective gap reduction."
    else:
        category = "LOW"
        interpretation = "Low Learning Gain: Limited advancement; supplementary targeted intervention recommended."

    return g_rounded, category, interpretation

class RemedialLearningService:
    @staticmethod
    def generate_remedial_learning_packs(
        db: Session,
        student_id: str,
        course_id: str,
        tau: float = 0.75
    ) -> List[RemedialPack]:
        """
        Stage 6: Formulate and rank learning gaps in descending order.
        If M_o,t < 0.30 -> recommend foundational learning pack.
        Else -> recommend reinforcement learning pack.
        Curate relevant course chunks and practice items.
        Delivered strictly to the authenticated student.
        """
        # Fetch student's mastery records for this course
        mastery_records = db.query(MasteryScore).filter(
            MasteryScore.student_id == student_id,
            MasteryScore.course_id == course_id
        ).all()

        objectives = db.query(CourseObjective).filter(CourseObjective.course_id == course_id).all()
        traits = db.query(Trait).all()
        obj_map = {o.id: o for o in objectives}
        trait_map = {t.id: t for t in traits}

        # If no mastery records yet, initialize with prior M = 0.5
        record_map = {(r.objective_id, r.trait_id): r for r in mastery_records}

        gap_candidates = []
        for obj in objectives:
            w_o = obj.weight if obj.weight is not None else 1.0
            for tr in traits:
                rec = record_map.get((obj.id, tr.id))
                m_val = rec.mastery_value if rec else 0.50
                g_val, rec_type = calculate_learning_gap(m_val, objective_weight=w_o, tau=tau)
                if g_val > 0.0:
                    gap_candidates.append({
                        "objective_id": obj.id,
                        "objective": obj,
                        "trait_id": tr.id,
                        "trait": tr,
                        "mastery_value": m_val,
                        "gap_score": g_val,
                        "recommendation_type": rec_type
                    })

        # Rank learning gaps in strictly descending order of G_o,t
        gap_candidates.sort(key=lambda x: x["gap_score"], reverse=True)

        packs = []
        for gap in gap_candidates:
            # Check if pack already exists
            existing_pack = db.query(RemedialPack).filter(
                RemedialPack.student_id == student_id,
                RemedialPack.course_id == course_id,
                RemedialPack.objective_id == gap["objective_id"],
                RemedialPack.trait_id == gap["trait_id"]
            ).first()

            if existing_pack:
                # Update gap score and recommendation if mastery changed
                existing_pack.gap_score = gap["gap_score"]
                existing_pack.recommendation_type = gap["recommendation_type"]
                packs.append(existing_pack)
                continue

            # Query relevant course material chunks mapped to this objective
            chunks = db.query(CourseMaterialChunk).filter(
                CourseMaterialChunk.course_id == course_id,
                CourseMaterialChunk.mapped_objective_id == gap["objective_id"]
            ).limit(3).all()

            reading_chunks = [
                {
                    "module_name": c.module_name or "Curriculum Module",
                    "content_snippet": c.content[:350] + "..." if len(c.content) > 350 else c.content
                }
                for c in chunks
            ]

            obj = gap["objective"]
            tr = gap["trait"]
            rec_type = gap["recommendation_type"]

            if rec_type == "FOUNDATIONAL":
                pack_title = f"Foundational Remedial Pack: {obj.code} Core Concepts"
                summary = (
                    f"Your mastery in {obj.code} ({tr.name}) is below 30%. This foundational module "
                    f"re-establishes prerequisite definitions, basic theoretical models, and fundamental reasoning rules."
                )
                key_concepts = [
                    f"Fundamental mathematical and architectural assumptions of {obj.code}",
                    f"Step-by-step deconstruction of {tr.name.lower()} primitives",
                    "Common conceptual pitfalls and boundary condition edge cases"
                ]
                practice_items = [
                    {
                        "question": f"State the primary invariant property governing {obj.code}.",
                        "conceptual_hint": f"Review definition: focus on basic state preservation aligned with {tr.name}."
                    },
                    {
                        "question": f"Identify the base condition when analyzing {obj.description[:40]}.",
                        "conceptual_hint": "Check the minimal input size or base recursion boundary."
                    }
                ]
            else:
                pack_title = f"Reinforcement Pack: {obj.code} Advanced {tr.name}"
                summary = (
                    f"You have moderate grasp in {obj.code}, but have not yet achieved the target threshold (tau = {int(tau*100)}%). "
                    f"This reinforcement pack focuses on rigorous proof techniques, optimization constraints, and trade-off analysis."
                )
                key_concepts = [
                    f"Optimization and complexity trade-offs in {obj.code}",
                    f"Rigorous verification of correctness applying {tr.name}",
                    "Asymptotic analysis under adversarial input distributions"
                ]
                practice_items = [
                    {
                        "question": f"Formulate the recurrence or transformation relation for {obj.code}.",
                        "conceptual_hint": f"Utilize inductive reasoning and {tr.name.lower()} structure."
                    },
                    {
                        "question": f"Prove why alternative heuristic approaches violate optimal bounds in {obj.code}.",
                        "conceptual_hint": "Construct a counterexample demonstrating violation of the optimal substructure property."
                    }
                ]

            content_payload = {
                "title": pack_title,
                "summary": summary,
                "key_concepts": key_concepts,
                "reading_chunks": reading_chunks,
                "practice_items": practice_items
            }

            db_pack = RemedialPack(
                student_id=student_id,
                course_id=course_id,
                objective_id=gap["objective_id"],
                trait_id=gap["trait_id"],
                gap_score=gap["gap_score"],
                recommendation_type=rec_type,
                content=content_payload,
                is_completed=False
            )
            db.add(db_pack)
            packs.append(db_pack)

        db.commit()
        return packs

    @staticmethod
    def start_post_assessment(
        db: Session,
        student_id: str,
        course_id: str
    ) -> Tuple[AssessmentSession, List[Question]]:
        """
        Stage 7: Conduct post-assessment with progressive hints.
        Re-verifies student's session and retrieves baseline pre_score.
        """
        # Retrieve the latest completed pre-assessment session to obtain baseline pre_score
        pre_session = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.course_id == course_id,
            AssessmentSession.status == AssessmentStatusEnum.COMPLETED,
            AssessmentSession.session_type == "PRE"
        ).order_by(AssessmentSession.completed_at.desc()).first()

        baseline_pre = pre_session.post_score if pre_session and pre_session.post_score is not None else 0.50

        # Check for active post-assessment session or create a new one
        post_session = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.course_id == course_id,
            AssessmentSession.session_type == "POST",
            AssessmentSession.status != AssessmentStatusEnum.COMPLETED
        ).first()

        if not post_session:
            post_session = AssessmentSession(
                student_id=student_id,
                course_id=course_id,
                session_type="POST",
                status=AssessmentStatusEnum.IN_PROGRESS,
                pre_score=baseline_pre
            )
            db.add(post_session)
            db.commit()
            db.refresh(post_session)
        else:
            if post_session.pre_score is None:
                post_session.pre_score = baseline_pre
                db.commit()

        # Fetch published questions for post-assessment
        questions = db.query(Question).filter(
            Question.course_id == course_id,
            Question.is_published == True
        ).all()

        return post_session, questions

    @staticmethod
    def process_post_assessment_submission(
        db: Session,
        session_id: str,
        student_id: str,
        submissions: List[Dict[str, Any]],
        tau: float = 0.75
    ) -> Dict[str, Any]:
        """
        Processes post-assessment submission:
        1. Evaluates responses using approved rubrics (server-side only).
        2. Calculates post_score in [0.0, 1.0].
        3. Updates mastery scores M_o,t.
        4. Calculates normalized learning gain g = (Post - Pre) / (1 - Pre).
        5. Handles Pre = 1.0 boundary case cleanly.
        """
        session = db.query(AssessmentSession).filter(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type == "POST"
        ).first()

        if not session:
            raise ValueError("Post-assessment session not found or unauthorized.")

        if session.status == AssessmentStatusEnum.COMPLETED:
            raise ValueError("Post-assessment session has already been completed.")

        # Process responses via MasteryEvaluationService
        eval_result = MasteryEvaluationService.process_submission(
            db=db,
            session_id=session_id,
            student_id=student_id,
            submissions=submissions,
            tau=tau
        )

        post_score = session.post_score or (eval_result["earned_points"] / eval_result["total_possible_points"] if eval_result["total_possible_points"] > 0 else 0.0)
        post_score = max(0.0, min(1.0, round(post_score, 4)))

        # Retrieve baseline Pre score
        pre_score = session.pre_score
        if pre_score is None:
            # Look up earlier completed PRE session
            pre_session = db.query(AssessmentSession).filter(
                AssessmentSession.student_id == student_id,
                AssessmentSession.course_id == session.course_id,
                AssessmentSession.session_type == "PRE",
                AssessmentSession.status == AssessmentStatusEnum.COMPLETED
            ).order_by(AssessmentSession.completed_at.desc()).first()
            pre_score = pre_session.post_score if pre_session and pre_session.post_score is not None else 0.50

        pre_score = max(0.0, min(1.0, round(pre_score, 4)))
        session.pre_score = pre_score

        # Calculate normalized gain g = (Post - Pre) / (1 - Pre)
        gain_val = None
        category = "PERFECT_BASELINE"
        interpretation = "Baseline pre-score was 100%; normalized gain is mathematically undefined."

        if abs(pre_score - 1.0) >= 1e-9:
            try:
                gain_val, category, interpretation = calculate_normalized_learning_gain(pre_score, post_score)
                session.normalized_gain = gain_val
            except ValueError:
                pass
        else:
            session.normalized_gain = None

        db.commit()

        eval_result["session_type"] = "POST"
        eval_result["pre_score"] = pre_score
        eval_result["post_score"] = post_score
        eval_result["normalized_gain"] = gain_val
        eval_result["gain_category"] = category
        eval_result["interpretation"] = interpretation

        return eval_result

    @staticmethod
    def generate_student_report(
        db: Session,
        student_id: str,
        course_id: str,
        tau: float = 0.75
    ) -> Dict[str, Any]:
        """
        Stage 8: Generates comprehensive assessment report for the student.
        Delivered strictly to the authenticated student.
        """
        student = db.query(User).filter(User.id == student_id).first()
        course = db.query(Course).filter(Course.id == course_id).first()
        if not student or not course:
            raise ValueError("Student or Course not found.")

        # Retrieve PRE and POST sessions
        pre_session = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.course_id == course_id,
            AssessmentSession.session_type == "PRE",
            AssessmentSession.status == AssessmentStatusEnum.COMPLETED
        ).order_by(AssessmentSession.completed_at.desc()).first()

        post_session = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.course_id == course_id,
            AssessmentSession.session_type == "POST",
            AssessmentSession.status == AssessmentStatusEnum.COMPLETED
        ).order_by(AssessmentSession.completed_at.desc()).first()

        pre_score = pre_session.post_score if pre_session and pre_session.post_score is not None else 0.50
        post_score = post_session.post_score if post_session else None

        gain_view = None
        if post_score is not None:
            if abs(pre_score - 1.0) < 1e-9:
                gain_view = {
                    "pre_score": pre_score,
                    "post_score": post_score,
                    "normalized_gain": None,
                    "gain_category": "PERFECT_BASELINE",
                    "interpretation": "Baseline pre-score was 100%; normalized gain is mathematically undefined."
                }
            else:
                g, cat, interp = calculate_normalized_learning_gain(pre_score, post_score)
                gain_view = {
                    "pre_score": pre_score,
                    "post_score": post_score,
                    "normalized_gain": g,
                    "gain_category": cat,
                    "interpretation": interp
                }

        # Mastery Progression
        objectives = db.query(CourseObjective).filter(CourseObjective.course_id == course_id).all()
        traits = db.query(Trait).all()
        current_mastery = db.query(MasteryScore).filter(
            MasteryScore.student_id == student_id,
            MasteryScore.course_id == course_id
        ).all()
        m_map = {(m.objective_id, m.trait_id): m for m in current_mastery}

        progression_items = []
        initial_gaps = 0
        resolved_gaps = 0

        for obj in objectives:
            for tr in traits:
                m_rec = m_map.get((obj.id, tr.id))
                post_m = m_rec.mastery_value if m_rec else 0.50
                pre_m = 0.50  # Baseline prior or historical pre
                delta = round(post_m - pre_m, 4)

                # Check gap status
                if post_m < tau:
                    initial_gaps += 1
                else:
                    resolved_gaps += 1

                progression_items.append({
                    "objective_code": obj.code,
                    "objective_description": obj.description,
                    "trait_name": tr.name,
                    "pre_mastery": pre_m,
                    "post_mastery": round(post_m, 4),
                    "delta": delta
                })

        # Remedial pack completion
        total_packs = db.query(RemedialPack).filter(
            RemedialPack.student_id == student_id,
            RemedialPack.course_id == course_id
        ).count()
        completed_packs = db.query(RemedialPack).filter(
            RemedialPack.student_id == student_id,
            RemedialPack.course_id == course_id,
            RemedialPack.is_completed == True
        ).count()

        return {
            "report_id": f"RPT-STU-{student.roll_number or student.id[:8]}",
            "student_name": student.full_name,
            "roll_number": student.roll_number,
            "course_code": course.course_code,
            "course_title": course.title,
            "pre_score": round(pre_score, 4),
            "post_score": round(post_score, 4) if post_score is not None else None,
            "gain": gain_view,
            "initial_gaps_count": initial_gaps,
            "resolved_gaps_count": resolved_gaps,
            "mastery_progression": progression_items,
            "remedial_packs_completed": completed_packs,
            "total_remedial_packs": total_packs,
            "generated_at": utcnow()
        }

    @staticmethod
    def generate_faculty_report(
        db: Session,
        course_id: str,
        tau: float = 0.75
    ) -> Dict[str, Any]:
        """
        Stage 8: Generates class-level cohort assessment report for authorized faculty.
        """
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Course not found.")

        enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.course_id == course_id).all()
        student_ids = [e.student_id for e in enrollments]
        total_enrolled = len(student_ids)

        if total_enrolled == 0:
            return {
                "course_id": course_id,
                "course_code": course.course_code,
                "course_title": course.title,
                "total_enrolled_students": 0,
                "completed_pre_count": 0,
                "completed_post_count": 0,
                "cohort_pre_average": 0.0,
                "cohort_post_average": 0.0,
                "cohort_normalized_gain_average": None,
                "gain_distribution": {
                    "high_gain_count": 0,
                    "medium_gain_count": 0,
                    "low_gain_count": 0,
                    "perfect_baseline_count": 0
                },
                "total_initial_gaps": 0,
                "total_resolved_gaps": 0,
                "gap_resolution_percentage": 0.0,
                "generated_at": utcnow()
            }

        # Query all completed PRE and POST sessions
        pre_sessions = db.query(AssessmentSession).filter(
            AssessmentSession.course_id == course_id,
            AssessmentSession.student_id.in_(student_ids),
            AssessmentSession.session_type == "PRE",
            AssessmentSession.status == AssessmentStatusEnum.COMPLETED
        ).all()

        post_sessions = db.query(AssessmentSession).filter(
            AssessmentSession.course_id == course_id,
            AssessmentSession.student_id.in_(student_ids),
            AssessmentSession.session_type == "POST",
            AssessmentSession.status == AssessmentStatusEnum.COMPLETED
        ).all()

        pre_scores = [s.post_score for s in pre_sessions if s.post_score is not None]
        post_scores = [s.post_score for s in post_sessions if s.post_score is not None]

        cohort_pre_avg = round(sum(pre_scores) / len(pre_scores), 4) if pre_scores else 0.50
        cohort_post_avg = round(sum(post_scores) / len(post_scores), 4) if post_scores else 0.0

        # Compute gains across students who completed both
        gain_distribution = {
            "high_gain_count": 0,
            "medium_gain_count": 0,
            "low_gain_count": 0,
            "perfect_baseline_count": 0
        }
        valid_gains = []

        for post_s in post_sessions:
            if post_s.normalized_gain is not None:
                valid_gains.append(post_s.normalized_gain)
                if post_s.normalized_gain >= 0.70:
                    gain_distribution["high_gain_count"] += 1
                elif post_s.normalized_gain >= 0.30:
                    gain_distribution["medium_gain_count"] += 1
                else:
                    gain_distribution["low_gain_count"] += 1
            elif post_s.pre_score is not None and abs(post_s.pre_score - 1.0) < 1e-9:
                gain_distribution["perfect_baseline_count"] += 1

        cohort_gain_avg = round(sum(valid_gains) / len(valid_gains), 4) if valid_gains else None

        # Aggregate gaps
        all_masteries = db.query(MasteryScore).filter(
            MasteryScore.course_id == course_id,
            MasteryScore.student_id.in_(student_ids)
        ).all()

        total_initial_gaps = sum(1 for m in all_masteries if m.gap_score > 0)
        total_resolved_gaps = sum(1 for m in all_masteries if m.mastery_value >= tau)
        resolution_pct = round((total_resolved_gaps / max(1, total_initial_gaps + total_resolved_gaps)) * 100, 2)

        return {
            "course_id": course_id,
            "course_code": course.course_code,
            "course_title": course.title,
            "total_enrolled_students": total_enrolled,
            "completed_pre_count": len(pre_sessions),
            "completed_post_count": len(post_sessions),
            "cohort_pre_average": cohort_pre_avg,
            "cohort_post_average": cohort_post_avg,
            "cohort_normalized_gain_average": cohort_gain_avg,
            "gain_distribution": gain_distribution,
            "total_initial_gaps": total_initial_gaps,
            "total_resolved_gaps": total_resolved_gaps,
            "gap_resolution_percentage": resolution_pct,
            "generated_at": utcnow()
        }

