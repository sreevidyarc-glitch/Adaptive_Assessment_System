from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, require_faculty
from app.models.user import User
from app.models.course import Course, CourseObjective, FacultyAssignment, CourseEnrollment, CourseMaterial, CourseMaterialChunk
from app.models.question import Question, Rubric, ModelAnswer
from app.models.assessment import MasteryScore
from app.schemas.faculty import (
    FacultyDashboardResponse,
    QuestionFacultyView,
    RubricResponse,
    ModelAnswerResponse,
    QuestionApprovalRequest,
    CourseSummary,
    CourseMaterialProcessingResponse,
    ObjectiveCoverageSummary,
    CoverageGapItem,
    ChunkMappingDetail,
    QuestionGenerationRequest,
    QuestionGenerationResponse,
    QuestionBatchApprovalRequest,
    ClassMasteryMatrixResponse,
    FacultyAssessmentReportResponse
)
from app.services.text_extraction_service import extract_text_from_file, parse_and_chunk_course_material
from app.services.nlp_service import nlp_service
from app.services.question_generation_service import generate_course_question_set
from app.services.mastery_evaluation_service import MasteryEvaluationService
from app.services.remedial_learning_service import RemedialLearningService

router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.get("/dashboard", response_model=FacultyDashboardResponse)
def get_faculty_dashboard(
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Returns faculty dashboard metrics, assigned courses, pending approvals,
    and recent questions including rubrics and model answers.
    """
    assignments = db.query(FacultyAssignment).filter(FacultyAssignment.faculty_id == current_user.id).all()
    assigned_course_ids = [a.course_id for a in assignments]

    course_summaries: List[CourseSummary] = []
    total_active_students = 0
    total_pending_approvals = 0

    courses = db.query(Course).filter(Course.id.in_(assigned_course_ids)).all() if assigned_course_ids else []

    for course in courses:
        student_count = db.query(CourseEnrollment).filter(CourseEnrollment.course_id == course.id).count()
        question_count = db.query(Question).filter(Question.course_id == course.id).count()
        pending_count = db.query(Question).filter(
            Question.course_id == course.id,
            Question.is_approved == False
        ).count()

        total_active_students += student_count
        total_pending_approvals += pending_count

        course_summaries.append(CourseSummary(
            id=course.id,
            course_code=course.course_code,
            title=course.title,
            description=course.description,
            student_count=student_count,
            question_count=question_count,
            pending_approvals=pending_count
        ))

    # Fetch recent questions with rubrics & model answers
    questions_query = db.query(Question).filter(
        Question.course_id.in_(assigned_course_ids)
    ).order_by(Question.created_at.desc()).limit(10).all() if assigned_course_ids else []

    question_views: List[QuestionFacultyView] = []
    for q in questions_query:
        rubric_view = None
        if q.rubric:
            rubric_view = RubricResponse(
                id=q.rubric.id,
                total_points=q.rubric.total_points,
                criteria=q.rubric.criteria
            )

        model_ans_view = None
        if q.model_answer:
            model_ans_view = ModelAnswerResponse(
                id=q.model_answer.id,
                content=q.model_answer.content,
                explanation=q.model_answer.explanation
            )

        question_views.append(QuestionFacultyView(
            id=q.id,
            course_id=q.course_id,
            objective_code=q.objective.code if q.objective else "N/A",
            objective_description=q.objective.description if q.objective else "N/A",
            trait_name=q.trait.name if q.trait else "General",
            prompt=q.prompt,
            hint1=q.hint1,
            hint2=q.hint2,
            is_approved=q.is_approved,
            is_published=q.is_published,
            created_at=q.created_at,
            rubric=rubric_view,
            model_answer=model_ans_view
        ))

    return FacultyDashboardResponse(
        faculty_name=current_user.full_name,
        department=current_user.department,
        assigned_courses=course_summaries,
        total_pending_approvals=total_pending_approvals,
        total_active_students=total_active_students,
        recent_questions=question_views
    )

@router.patch("/questions/{question_id}/approve", response_model=QuestionFacultyView)
def approve_question(
    question_id: str,
    payload: QuestionApprovalRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Approves or publishes a generated question set.
    Requires authenticated faculty assignment to the question's course.
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    # Verify faculty is assigned to this course
    assignment = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_id == current_user.id,
        FacultyAssignment.course_id == question.course_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You are not assigned to instruct this course."
        )

    question.is_approved = payload.is_approved
    if payload.is_approved:
        question.approved_by = current_user.id
        question.approved_at = datetime.now(timezone.utc)
    if payload.is_published is not None:
        question.is_published = payload.is_published

    db.commit()
    db.refresh(question)

    rubric_view = RubricResponse(
        id=question.rubric.id,
        total_points=question.rubric.total_points,
        criteria=question.rubric.criteria
    ) if question.rubric else None

    model_ans_view = ModelAnswerResponse(
        id=question.model_answer.id,
        content=question.model_answer.content,
        explanation=question.model_answer.explanation
    ) if question.model_answer else None

    return QuestionFacultyView(
        id=question.id,
        course_id=question.course_id,
        objective_code=question.objective.code if question.objective else "N/A",
        objective_description=question.objective.description if question.objective else "N/A",
        trait_name=question.trait.name if question.trait else "General",
        prompt=question.prompt,
        hint1=question.hint1,
        hint2=question.hint2,
        is_approved=question.is_approved,
        is_published=question.is_published,
        created_at=question.created_at,
        rubric=rubric_view,
        model_answer=model_ans_view
    )

# -------------------------------------------------------------
# Course Material Processing & Learning Objective Mapping APIs
# -------------------------------------------------------------

@router.post("/courses/{course_id}/materials/upload", response_model=CourseMaterialProcessingResponse)
async def upload_and_process_course_material(
    course_id: str,
    file: UploadFile = File(...),
    similarity_threshold: float = Form(0.35),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Stage 1 & 2 of Integrated Algorithm:
    1. Authenticates faculty and confirms course assignment.
    2. Extracts text from PDF, DOCX, or TXT file.
    3. Splits text into module-wise paragraph/sentence chunks S.
    4. Computes cosine similarity with each objective o_j.
    5. Assigns s_i to best-matching objective meeting the similarity threshold.
    6. Identifies coverage gaps (objectives with 0 matching chunks).
    7. Stores chunks with module identifiers in the database.
    """
    # Authorization Check: verify faculty is assigned to this course (Spec Line 41-46)
    assignment = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_id == current_user.id,
        FacultyAssignment.course_id == course_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UnauthorizedCourseAccess: You are not assigned to instruct this course."
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    # 1. Read file bytes and extract text
    file_bytes = await file.read()
    try:
        raw_text = extract_text_from_file(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file contains no extractable text."
        )

    # 2. Split into module-wise paragraph/sentence chunks S
    raw_chunks = parse_and_chunk_course_material(raw_text)
    if not raw_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate valid content chunks from the uploaded document."
        )

    # 3. Fetch Course Objectives
    objectives = db.query(CourseObjective).filter(CourseObjective.course_id == course_id).all()
    if not objectives:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This course has no defined learning objectives. Please configure objectives first."
        )

    objectives_data = [
        {"id": o.id, "code": o.code, "description": o.description, "weight": o.weight}
        for o in objectives
    ]

    # 4. Compute Cosine Similarity and Map Chunks to Objectives
    mapping_result = nlp_service.map_chunks_to_objectives(
        chunks=raw_chunks,
        objectives=objectives_data,
        similarity_threshold=similarity_threshold
    )

    # 5. Persist CourseMaterial and CourseMaterialChunk in DB
    ext = file.filename.lower().split('.')[-1]
    material = CourseMaterial(
        course_id=course_id,
        filename=file.filename,
        file_type=ext,
        uploaded_by=current_user.id
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    saved_chunks: List[ChunkMappingDetail] = []
    for chunk_data in mapping_result["mapped_chunks"]:
        db_chunk = CourseMaterialChunk(
            material_id=material.id,
            course_id=course_id,
            module_name=chunk_data["module_name"],
            chunk_index=chunk_data["chunk_index"],
            content=chunk_data["content"],
            mapped_objective_id=chunk_data["mapped_objective_id"],
            similarity_score=chunk_data["similarity_score"]
        )
        db.add(db_chunk)
        db.flush()

        saved_chunks.append(ChunkMappingDetail(
            id=db_chunk.id,
            module_name=db_chunk.module_name,
            chunk_index=db_chunk.chunk_index,
            content=db_chunk.content,
            mapped_objective_id=db_chunk.mapped_objective_id,
            mapped_objective_code=chunk_data["mapped_objective_code"],
            similarity_score=db_chunk.similarity_score,
            is_mapped=chunk_data["is_mapped"]
        ))

    db.commit()

    return CourseMaterialProcessingResponse(
        material_id=material.id,
        filename=material.filename,
        total_chunks=len(saved_chunks),
        similarity_threshold=similarity_threshold,
        objective_summaries=[
            ObjectiveCoverageSummary(**s) for s in mapping_result["objective_summaries"]
        ],
        coverage_gaps=[
            CoverageGapItem(**g) for g in mapping_result["coverage_gaps"]
        ],
        chunks=saved_chunks
    )

@router.get("/courses/{course_id}/materials/mapping", response_model=CourseMaterialProcessingResponse)
def get_course_material_mapping(
    course_id: str,
    material_id: Optional[str] = Query(None),
    similarity_threshold: float = Query(0.35, ge=0.05, le=0.95),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Retrieves existing course material chunks and computes current coverage status
    and coverage gaps against the configurable similarity threshold.
    """
    assignment = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_id == current_user.id,
        FacultyAssignment.course_id == course_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UnauthorizedCourseAccess: You are not assigned to instruct this course."
        )

    objectives = db.query(CourseObjective).filter(CourseObjective.course_id == course_id).all()
    objectives_data = [
        {"id": o.id, "code": o.code, "description": o.description, "weight": o.weight}
        for o in objectives
    ]

    # Target material
    material_query = db.query(CourseMaterial).filter(CourseMaterial.course_id == course_id)
    if material_id:
        target_material = material_query.filter(CourseMaterial.id == material_id).first()
    else:
        target_material = material_query.order_by(CourseMaterial.uploaded_at.desc()).first()

    if not target_material:
        return CourseMaterialProcessingResponse(
            material_id=None,
            filename="No material uploaded yet",
            total_chunks=0,
            similarity_threshold=similarity_threshold,
            objective_summaries=[
                ObjectiveCoverageSummary(
                    objective_id=o["id"],
                    code=o["code"],
                    description=o["description"],
                    weight=o["weight"],
                    mapped_chunk_count=0,
                    max_similarity=0.0,
                    is_gap=True
                )
                for o in objectives_data
            ],
            coverage_gaps=[
                CoverageGapItem(objective_id=o["id"], code=o["code"], description=o["description"])
                for o in objectives_data
            ],
            chunks=[]
        )

    chunks = db.query(CourseMaterialChunk).filter(
        CourseMaterialChunk.material_id == target_material.id
    ).order_by(CourseMaterialChunk.chunk_index.asc()).all()

    # Re-evaluate mapping with current threshold
    raw_chunks = [
        {"id": c.id, "module_name": c.module_name, "chunk_index": c.chunk_index, "content": c.content}
        for c in chunks
    ]
    mapping_result = nlp_service.map_chunks_to_objectives(
        chunks=raw_chunks,
        objectives=objectives_data,
        similarity_threshold=similarity_threshold
    )

    chunk_details = [
        ChunkMappingDetail(
            id=c["id"],
            module_name=c["module_name"],
            chunk_index=c["chunk_index"],
            content=c["content"],
            mapped_objective_id=c["mapped_objective_id"],
            mapped_objective_code=c["mapped_objective_code"],
            similarity_score=c["similarity_score"],
            is_mapped=c["is_mapped"]
        )
        for c in mapping_result["mapped_chunks"]
    ]

    return CourseMaterialProcessingResponse(
        material_id=target_material.id,
        filename=target_material.filename,
        total_chunks=len(chunk_details),
        similarity_threshold=similarity_threshold,
        objective_summaries=[
            ObjectiveCoverageSummary(**s) for s in mapping_result["objective_summaries"]
        ],
        coverage_gaps=[
            CoverageGapItem(**g) for g in mapping_result["coverage_gaps"]
        ],
        chunks=chunk_details
    )


# -------------------------------------------------------------
# Adaptive Question Generation & Faculty Approval APIs
# -------------------------------------------------------------

@router.post("/courses/{course_id}/questions/generate", response_model=QuestionGenerationResponse)
def generate_questions_for_course(
    course_id: str,
    payload: QuestionGenerationRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Executes Stages 3 & 4 of Integrated Algorithm:
    - Allocates questions across objectives using the largest remainder method.
    - Allocates questions across traits using remaining quota deficits.
    - Retrieves relevant course chunks.
    - Generates Question, Rubric, Model Answer, Hints via LLM.
    - Runs 4 validation checks (schema, hint leakage, rubric sanity, duplicate).
    - Retries up to 3 times on validation failure.
    - Stores questions in DB pending faculty approval.
    """
    # Verify faculty assignment
    assignment = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_id == current_user.id,
        FacultyAssignment.course_id == course_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UnauthorizedCourseAccess: You are not assigned to instruct this course."
        )

    try:
        result = generate_course_question_set(
            course_id=course_id,
            total_questions=payload.total_questions,
            db=db,
            objective_weights=payload.objective_weights,
            trait_weights=payload.trait_weights
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {e}")

@router.get("/courses/{course_id}/questions", response_model=List[QuestionFacultyView])
def get_course_questions_for_faculty(
    course_id: str,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Lists all questions for a course with full privileged rubrics and model answers.
    Visible to authorized faculty only.
    """
    assignment = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_id == current_user.id,
        FacultyAssignment.course_id == course_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UnauthorizedCourseAccess: You are not assigned to instruct this course."
        )

    questions = db.query(Question).filter(Question.course_id == course_id).order_by(
        Question.created_at.desc()
    ).all()

    views = []
    for q in questions:
        rubric_view = RubricResponse(
            id=q.rubric.id,
            total_points=q.rubric.total_points,
            criteria=q.rubric.criteria
        ) if q.rubric else None

        model_ans_view = ModelAnswerResponse(
            id=q.model_answer.id,
            content=q.model_answer.content,
            explanation=q.model_answer.explanation
        ) if q.model_answer else None

        views.append(QuestionFacultyView(
            id=q.id,
            course_id=q.course_id,
            objective_code=q.objective.code if q.objective else "CO",
            objective_description=q.objective.description if q.objective else "N/A",
            trait_name=q.trait.name if q.trait else "General",
            prompt=q.prompt,
            hint1=q.hint1,
            hint2=q.hint2,
            is_approved=q.is_approved,
            is_published=q.is_published,
            created_at=q.created_at,
            rubric=rubric_view,
            model_answer=model_ans_view
        ))
    return views

@router.post("/courses/{course_id}/questions/batch-approve")
def batch_approve_questions(
    course_id: str,
    payload: QuestionBatchApprovalRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Batch approves and/or publishes selected questions.
    """
    assignment = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_id == current_user.id,
        FacultyAssignment.course_id == course_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UnauthorizedCourseAccess: You are not assigned to instruct this course."
        )

    questions = db.query(Question).filter(
        Question.course_id == course_id,
        Question.id.in_(payload.question_ids)
    ).all()

    now = datetime.now(timezone.utc)
    for q in questions:
        q.is_approved = payload.is_approved
        if payload.is_approved:
            q.approved_by = current_user.id
            q.approved_at = now
        q.is_published = payload.is_published

    db.commit()
    return {
        "status": "SUCCESS",
        "approved_count": len(questions),
        "is_published": payload.is_published
    }

@router.get("/courses/{course_id}/mastery-matrix", response_model=ClassMasteryMatrixResponse)
def get_class_mastery_matrix_endpoint(
    course_id: str,
    tau: float = Query(0.75, ge=0.0, le=1.0),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated class-level mastery matrix for an assigned course.
    Verifies faculty assignment to course.
    """
    assignment = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_id == current_user.id,
        FacultyAssignment.course_id == course_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UnauthorizedCourseAccess: You are not assigned to instruct this course."
        )

    return MasteryEvaluationService.get_class_mastery_matrix(
        db=db,
        course_id=course_id,
        tau=tau
    )

@router.get("/courses/{course_id}/assessment-report", response_model=FacultyAssessmentReportResponse)
def get_faculty_assessment_report_endpoint(
    course_id: str,
    tau: float = Query(0.75, ge=0.0, le=1.0),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    [AUTH] Stage 8: Generates cohort-level assessment and learning gain report.
    Authorized faculty can view class-level reports for assigned courses.
    """
    assignment = db.query(FacultyAssignment).filter(
        FacultyAssignment.faculty_id == current_user.id,
        FacultyAssignment.course_id == course_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UnauthorizedCourseAccess: You are not assigned to instruct this course."
        )

    return RemedialLearningService.generate_faculty_report(
        db=db,
        course_id=course_id,
        tau=tau
    )


