from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime

class RubricResponse(BaseModel):
    id: str
    total_points: float
    criteria: List[Dict[str, Any]]

    model_config = {"from_attributes": True}

class ModelAnswerResponse(BaseModel):
    id: str
    content: str
    explanation: Optional[str] = None

    model_config = {"from_attributes": True}

class QuestionFacultyView(BaseModel):
    id: str
    course_id: str
    objective_code: str
    objective_description: str
    trait_name: Optional[str] = None
    prompt: str
    hint1: Optional[str] = None
    hint2: Optional[str] = None
    is_approved: bool
    is_published: bool
    created_at: datetime
    # Privileged data: Accessible only to authorized Faculty
    rubric: Optional[RubricResponse] = None
    model_answer: Optional[ModelAnswerResponse] = None

class CourseSummary(BaseModel):
    id: str
    course_code: str
    title: str
    description: Optional[str] = None
    student_count: int
    question_count: int
    pending_approvals: int

class FacultyDashboardResponse(BaseModel):
    faculty_name: str
    department: Optional[str] = None
    assigned_courses: List[CourseSummary]
    total_pending_approvals: int
    total_active_students: int
    recent_questions: List[QuestionFacultyView]

class QuestionApprovalRequest(BaseModel):
    is_approved: bool
    is_published: Optional[bool] = False

# Course Material Processing & Objective Mapping Schemas

class ChunkMappingDetail(BaseModel):
    id: Optional[str] = None
    module_name: str
    chunk_index: int
    content: str
    mapped_objective_id: Optional[str] = None
    mapped_objective_code: Optional[str] = None
    similarity_score: Optional[float] = None
    is_mapped: bool

class CoverageGapItem(BaseModel):
    objective_id: str
    code: str
    description: str

class ObjectiveCoverageSummary(BaseModel):
    objective_id: str
    code: str
    description: str
    weight: float = 1.0
    mapped_chunk_count: int
    max_similarity: float
    is_gap: bool

class CourseMaterialProcessingResponse(BaseModel):
    material_id: Optional[str] = None
    filename: str
    total_chunks: int
    similarity_threshold: float
    objective_summaries: List[ObjectiveCoverageSummary]
    coverage_gaps: List[CoverageGapItem]
    chunks: List[ChunkMappingDetail]


# Adaptive Question Generation Schemas

class QuestionGenerationRequest(BaseModel):
    total_questions: int = 5
    objective_weights: Optional[Dict[str, float]] = None
    trait_weights: Optional[Dict[str, float]] = None

class AllocationSummaryItem(BaseModel):
    objective_id: str
    objective_code: str
    question_count: int

class GeneratedQuestionItem(BaseModel):
    id: str
    objective_code: str
    trait_name: str
    prompt: str
    hint1: Optional[str] = None
    hint2: Optional[str] = None
    generation_retries: int = 0
    validation_status: str = "PASSED"
    validation_notes: Optional[str] = None
    rubric: Optional[RubricResponse] = None
    model_answer: Optional[ModelAnswerResponse] = None

class QuestionGenerationResponse(BaseModel):
    course_id: str
    total_requested: int
    total_generated: int
    unresolved_failures_count: int
    allocations: List[AllocationSummaryItem]
    questions: List[GeneratedQuestionItem]

class QuestionBatchApprovalRequest(BaseModel):
    question_ids: List[str]
    is_approved: bool = True
    is_published: bool = True

# Class Mastery Matrix Schemas (Faculty Aggregated View)

class ClassTraitSummary(BaseModel):
    trait_id: str
    trait_code: str
    trait_name: str
    mean_mastery: float
    min_mastery: float
    max_mastery: float
    students_with_gaps: int
    foundational_remedial_count: int
    reinforcement_count: int

class ClassObjectiveRow(BaseModel):
    objective_id: str
    objective_code: str
    objective_description: str
    priority_weight: float
    traits: List[ClassTraitSummary]

class ClassMasteryMatrixResponse(BaseModel):
    course_id: str
    total_enrolled_students: int
    tau_threshold: float = 0.75
    matrix: List[ClassObjectiveRow]
    summary: Optional[str] = None

# Faculty Assessment Report Schemas

class GainDistributionStats(BaseModel):
    high_gain_count: int
    medium_gain_count: int
    low_gain_count: int
    perfect_baseline_count: int

class FacultyAssessmentReportResponse(BaseModel):
    course_id: str
    course_code: str
    course_title: str
    total_enrolled_students: int
    completed_pre_count: int
    completed_post_count: int
    cohort_pre_average: float
    cohort_post_average: float
    cohort_normalized_gain_average: Optional[float] = None
    gain_distribution: GainDistributionStats
    total_initial_gaps: int
    total_resolved_gaps: int
    gap_resolution_percentage: float
    generated_at: datetime


