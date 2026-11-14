from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_student
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.models.question import Question
from app.models.assessment import MasteryScore, AssessmentSession, AssessmentStatusEnum, RemedialPack
from app.schemas.student import (
    StudentDashboardResponse,
    StudentCourseView,
    StudentQuestionView,
    MasteryItem,
    StartAssessmentResponse,
    AssessmentSubmissionRequest,
    AssessmentSubmissionResponse,
    StudentMasteryMatrixResponse,
    RemedialPackView,
    StudentAssessmentReportResponse
)
from app.services.mastery_evaluation_service import MasteryEvaluationService
from app.services.remedial_learning_service import RemedialLearningService

router = APIRouter(prefix="/student", tags=["Student"])

@router.get("/dashboard", response_model=StudentDashboardResponse)
def get_student_dashboard(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Returns student dashboard metrics, enrolled courses, and personal mastery breakdown.
    Adheres strictly to Privacy Requirement:
    - Student can view only their own mastery matrix M
    - Rubrics and model answers are never serialized.
    """
    enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.student_id == current_user.id).all()
    enrolled_courses: List[StudentCourseView] = []
    course_ids = []

    for enr in enrollments:
        course = db.query(Course).filter(Course.id == enr.course_id).first()
        if course:
            course_ids.append(course.id)
            enrolled_courses.append(StudentCourseView(
                id=course.id,
                course_code=course.course_code,
                title=course.title,
                description=course.description,
                enrolled_at=enr.enrolled_at
            ))

    # Fetch student's own mastery scores
    mastery_records = db.query(MasteryScore).filter(
        MasteryScore.student_id == current_user.id
    ).all()

    mastery_items: List[MasteryItem] = []
    total_val = 0.0

    for m in mastery_records:
        total_val += m.mastery_value
        mastery_items.append(MasteryItem(
            objective_code=m.objective.code if m.objective else "CO",
            objective_description=m.objective.description if m.objective else "N/A",
            trait_name=m.trait.name if m.trait else "General Mastery",
            mastery_value=round(m.mastery_value, 2),
            gap_score=round(m.gap_score, 2),
            recommendation_type=m.recommendation_type
        ))

    overall_avg = round(total_val / len(mastery_records), 2) if mastery_records else 0.0

    # Count active assessments
    active_assessments = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == current_user.id,
        AssessmentSession.status != AssessmentStatusEnum.COMPLETED
    ).count()

    return StudentDashboardResponse(
        student_name=current_user.full_name,
        roll_number=current_user.roll_number,
        department=current_user.department,
        enrolled_courses=enrolled_courses,
        overall_mastery_average=overall_avg,
        mastery_breakdown=mastery_items,
        active_assessments_count=active_assessments
    )

@router.get("/courses/{course_id}/questions", response_model=List[StudentQuestionView])
def get_course_questions_for_student(
    course_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Returns published questions for an enrolled course.
    STRICT PRIVACY: Rubrics and Model Answers are completely excluded.
    """
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You are not enrolled in this course."
        )

    questions = db.query(Question).filter(
        Question.course_id == course_id,
        Question.is_published == True
    ).all()

    return [
        StudentQuestionView(
            id=q.id,
            course_id=q.course_id,
            objective_code=q.objective.code if q.objective else "CO",
            trait_name=q.trait.name if q.trait else "General",
            prompt=q.prompt,
            hint1=q.hint1,
            hint2=q.hint2
        )
        for q in questions
    ]

@router.post("/courses/{course_id}/assessments/start", response_model=StartAssessmentResponse)
def start_assessment_session(
    course_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Initializes or resumes an assessment session for the student.
    Returns the set of approved & published questions.
    STRICT PRIVACY: Rubrics and Model Answers are never sent to the client.
    """
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You are not enrolled in this course."
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    # Check for existing uncompleted session
    session = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == current_user.id,
        AssessmentSession.course_id == course_id,
        AssessmentSession.status != AssessmentStatusEnum.COMPLETED
    ).first()

    if not session:
        session = AssessmentSession(
            student_id=current_user.id,
            course_id=course_id,
            status=AssessmentStatusEnum.IN_PROGRESS
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Fetch approved and published questions
    questions = db.query(Question).filter(
        Question.course_id == course_id,
        Question.is_published == True
    ).all()

    question_views = [
        StudentQuestionView(
            id=q.id,
            course_id=q.course_id,
            objective_code=q.objective.code if q.objective else "CO",
            trait_name=q.trait.name if q.trait else "General",
            prompt=q.prompt,
            hint1=q.hint1,
            hint2=q.hint2
        )
        for q in questions
    ]

    return StartAssessmentResponse(
        session_id=session.id,
        course_id=course.id,
        course_code=course.course_code,
        course_title=course.title,
        status=session.status.value,
        questions=question_views
    )

@router.post("/assessments/{session_id}/submit", response_model=AssessmentSubmissionResponse)
def submit_assessment_session(
    session_id: str,
    submission_data: AssessmentSubmissionRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Submits student responses for an active assessment session.
    Evaluates responses against approved rubrics on the server.
    Calculates f_i = earned / total points.
    Calculates M_o,t = (1 + sum(w_i * f_i)) / (2 + sum(w_i)).
    Updates separate MasteryScore for each (o, t).
    """
    try:
        raw_submissions = [r.model_dump() for r in submission_data.responses]
        result = MasteryEvaluationService.process_submission(
            db=db,
            session_id=session_id,
            student_id=current_user.id,
            submissions=raw_submissions
        )
        return AssessmentSubmissionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process assessment submission: {str(e)}"
        )

@router.get("/courses/{course_id}/mastery-matrix", response_model=StudentMasteryMatrixResponse)
def get_student_mastery_matrix_endpoint(
    course_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Returns personal |O| x |T| mastery matrix and ranked learning gaps for the authenticated student.
    PRIVACY GUARANTEE: Student can only view their own mastery records.
    """
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You are not enrolled in this course."
        )

    return MasteryEvaluationService.get_student_mastery_matrix(
        db=db,
        student_id=current_user.id,
        course_id=course_id
    )

# Stage 6: Personalized Remedial Learning Packs

@router.get("/courses/{course_id}/remedial-packs", response_model=List[RemedialPackView])
def get_student_remedial_packs(
    course_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Returns personalized remedial learning packs formulated from ranked learning gaps.
    STRICT PRIVACY: Delivered exclusively to the authenticated student.
    """
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You are not enrolled in this course."
        )

    packs = RemedialLearningService.generate_remedial_learning_packs(
        db=db,
        student_id=current_user.id,
        course_id=course_id
    )

    pack_views = []
    for p in packs:
        content = p.content if isinstance(p.content, dict) else {}
        pack_views.append(RemedialPackView(
            id=p.id,
            course_id=p.course_id,
            objective_id=p.objective_id,
            objective_code=p.objective.code if p.objective else "CO",
            objective_description=p.objective.description if p.objective else "N/A",
            trait_name=p.trait.name if p.trait else "General Trait",
            gap_score=round(p.gap_score, 2),
            recommendation_type=p.recommendation_type,
            title=content.get("title", "Remedial Module"),
            summary=content.get("summary", ""),
            key_concepts=content.get("key_concepts", []),
            reading_chunks=content.get("reading_chunks", []),
            practice_items=content.get("practice_items", []),
            is_completed=p.is_completed,
            created_at=p.created_at,
            completed_at=p.completed_at
        ))

    return pack_views

@router.patch("/remedial-packs/{pack_id}/complete")
def complete_remedial_pack(
    pack_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Marks a remedial learning pack as completed by the student.
    """
    pack = db.query(RemedialPack).filter(
        RemedialPack.id == pack_id,
        RemedialPack.student_id == current_user.id
    ).first()

    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remedial pack not found or unauthorized."
        )

    pack.is_completed = True
    pack.completed_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "SUCCESS", "pack_id": pack.id, "is_completed": True}

# Stage 7: Progressive Hints Post-Assessment & Normalized Learning Gain

@router.post("/courses/{course_id}/post-assessments/start", response_model=StartAssessmentResponse)
def start_post_assessment_endpoint(
    course_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    [AUTH] Re-verifies student session token and initiates post-assessment.
    Conducts post-assessment with progressive hints (Hint 1 and Hint 2).
    STRICT PRIVACY: Rubrics and Model Answers are stripped.
    """
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You are not enrolled in this course."
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    post_session, questions = RemedialLearningService.start_post_assessment(
        db=db,
        student_id=current_user.id,
        course_id=course_id
    )

    question_views = [
        StudentQuestionView(
            id=q.id,
            course_id=q.course_id,
            objective_code=q.objective.code if q.objective else "CO",
            trait_name=q.trait.name if q.trait else "General",
            prompt=q.prompt,
            hint1=q.hint1,
            hint2=q.hint2
        )
        for q in questions
    ]

    return StartAssessmentResponse(
        session_id=post_session.id,
        course_id=course.id,
        course_code=course.course_code,
        course_title=course.title,
        status=post_session.status.value,
        session_type="POST",
        questions=question_views
    )

@router.post("/post-assessments/{session_id}/submit", response_model=AssessmentSubmissionResponse)
def submit_post_assessment_endpoint(
    session_id: str,
    submission_data: AssessmentSubmissionRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Submits post-assessment answers.
    Evaluates rubrics, computes post-score, and calculates normalized learning gain:
    g = (Post - Pre) / (1 - Pre)
    """
    try:
        raw_submissions = [r.model_dump() for r in submission_data.responses]
        result = RemedialLearningService.process_post_assessment_submission(
            db=db,
            session_id=session_id,
            student_id=current_user.id,
            submissions=raw_submissions
        )
        return AssessmentSubmissionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit post-assessment: {str(e)}"
        )

# Stage 8: Student Assessment Report

@router.get("/courses/{course_id}/assessment-report", response_model=StudentAssessmentReportResponse)
def get_student_assessment_report_endpoint(
    course_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Generates personal assessment report showing pre-score, post-score,
    normalized learning gain, and mastery progression.
    STRICT PRIVACY: Student can view their own assessment report only.
    """
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You are not enrolled in this course."
        )

    try:
        return RemedialLearningService.generate_student_report(
            db=db,
            student_id=current_user.id,
            course_id=course_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

