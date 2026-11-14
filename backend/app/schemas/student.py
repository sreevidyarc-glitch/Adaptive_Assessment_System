from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class StudentCourseView(BaseModel):
    id: str
    course_code: str
    title: str
    description: Optional[str] = None
    enrolled_at: datetime

class StudentQuestionView(BaseModel):
    """
    CRITICAL PRIVACY SAFEGUARD:
    Rubrics and Model Answers are explicitly omitted from this schema.
    Students can only see the question prompt and available hints.
    """
    id: str
    course_id: str
    objective_code: str
    trait_name: Optional[str] = None
    prompt: str
    hint1: Optional[str] = None
    hint2: Optional[str] = None

class MasteryItem(BaseModel):
    objective_code: str
    objective_description: str
    trait_name: str
    mastery_value: float  # M_o,t in [0.0, 1.0]
    gap_score: float      # G_o,t
    recommendation_type: str  # FOUNDATIONAL or REINFORCEMENT

class StudentDashboardResponse(BaseModel):
    student_name: str
    roll_number: Optional[str] = None
    department: Optional[str] = None
    enrolled_courses: List[StudentCourseView]
    overall_mastery_average: float
    mastery_breakdown: List[MasteryItem]
    active_assessments_count: int

# Assessment Execution Schemas

class StartAssessmentResponse(BaseModel):
    session_id: str
    course_id: str
    course_code: str
    course_title: str
    status: str
    session_type: str = "PRE"
    questions: List[StudentQuestionView]

class QuestionAnswerSubmission(BaseModel):
    question_id: str
    response_text: str
    hints_used: int = 0

class AssessmentSubmissionRequest(BaseModel):
    responses: List[QuestionAnswerSubmission]

class QuestionEvaluationResult(BaseModel):
    question_id: str
    earned_points: float
    total_points: float
    fraction_achieved: float  # f_i = earned / total
    hints_used: int

class AssessmentSubmissionResponse(BaseModel):
    session_id: str
    course_id: str
    status: str
    session_type: str = "PRE"
    total_questions: int
    earned_points: float
    total_possible_points: float
    overall_percentage: float
    pre_score: Optional[float] = None
    post_score: Optional[float] = None
    normalized_gain: Optional[float] = None
    gain_category: Optional[str] = None
    results: List[QuestionEvaluationResult]

# Mastery Matrix Schemas (Personal - Student View)

class StudentMasteryCell(BaseModel):
    trait_id: Optional[str] = None
    trait_code: Optional[str] = None
    trait_name: Optional[str] = None
    mastery_value: float  # M_o,t
    gap_score: float      # G_o,t
    recommendation_type: str  # FOUNDATIONAL or REINFORCEMENT

class StudentMasteryRow(BaseModel):
    objective_id: str
    objective_code: str
    objective_description: str
    priority_weight: float
    traits: List[StudentMasteryCell]

class RankedLearningGap(BaseModel):
    objective_id: str
    objective_code: str
    objective_description: str
    trait_code: Optional[str] = None
    trait_name: Optional[str] = None
    mastery_value: float
    gap_score: float
    recommendation_type: str

class StudentMasteryMatrixResponse(BaseModel):
    course_id: str
    overall_average_mastery: float
    tau_threshold: float
    matrix: List[StudentMasteryRow]
    ranked_learning_gaps: List[RankedLearningGap]

# Remedial Learning Pack Schemas

class RemedialReadingChunk(BaseModel):
    module_name: str
    content_snippet: str

class RemedialPracticeItem(BaseModel):
    question: str
    conceptual_hint: str

class RemedialPackView(BaseModel):
    id: str
    course_id: str
    objective_id: str
    objective_code: str
    objective_description: str
    trait_name: str
    gap_score: float
    recommendation_type: str  # FOUNDATIONAL or REINFORCEMENT
    title: str
    summary: str
    key_concepts: List[str]
    reading_chunks: List[RemedialReadingChunk]
    practice_items: List[RemedialPracticeItem]
    is_completed: bool
    created_at: datetime
    completed_at: Optional[datetime] = None

# Normalized Gain & Assessment Report Schemas

class NormalizedGainView(BaseModel):
    pre_score: float
    post_score: float
    normalized_gain: Optional[float] = None
    gain_category: str  # HIGH, MEDIUM, LOW, or PERFECT_BASELINE
    interpretation: str

class MasteryProgressionItem(BaseModel):
    objective_code: str
    objective_description: str
    trait_name: str
    pre_mastery: float
    post_mastery: float
    delta: float

class StudentAssessmentReportResponse(BaseModel):
    report_id: str
    student_name: str
    roll_number: Optional[str] = None
    course_code: str
    course_title: str
    pre_score: float
    post_score: Optional[float] = None
    gain: Optional[NormalizedGainView] = None
    initial_gaps_count: int
    resolved_gaps_count: int
    mastery_progression: List[MasteryProgressionItem]
    remedial_packs_completed: int
    total_remedial_packs: int
    generated_at: datetime
