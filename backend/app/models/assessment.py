import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, Integer, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class AssessmentStatusEnum(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(AssessmentStatusEnum), default=AssessmentStatusEnum.NOT_STARTED)
    session_type = Column(String(20), default="PRE")  # PRE or POST
    
    pre_score = Column(Float, nullable=True)
    post_score = Column(Float, nullable=True)
    normalized_gain = Column(Float, nullable=True)  # g = (Post - Pre) / (1 - Pre)
    
    started_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    responses = relationship("StudentResponse", back_populates="session", cascade="all, delete-orphan")

class StudentResponse(Base):
    __tablename__ = "student_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    response_text = Column(Text, nullable=False)
    hints_used = Column(Integer, default=0)
    earned_points = Column(Float, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("AssessmentSession", back_populates="responses")

class MasteryScore(Base):
    """
    Stores Objective-Trait mastery (M_o,t) and gap score (G_o,t).
    Private to student; class aggregates accessible by authorized faculty.
    """
    __tablename__ = "mastery_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    objective_id = Column(String(36), ForeignKey("course_objectives.id", ondelete="CASCADE"), nullable=False)
    trait_id = Column(String(36), ForeignKey("traits.id", ondelete="CASCADE"), nullable=True)
    
    mastery_value = Column(Float, nullable=False, default=0.5)  # M_o,t in [0, 1]
    gap_score = Column(Float, nullable=False, default=0.0)      # G_o,t = (tau - M) * w_o
    recommendation_type = Column(String(50), default="REINFORCEMENT")  # FOUNDATIONAL or REINFORCEMENT
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student = relationship("User", back_populates="mastery_scores")
    objective = relationship("CourseObjective")
    trait = relationship("Trait")

class RemedialPack(Base):
    """
    Personalized remedial learning packs generated based on identified gaps.
    Delivered exclusively to the authenticated student.
    """
    __tablename__ = "remedial_packs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    objective_id = Column(String(36), ForeignKey("course_objectives.id", ondelete="CASCADE"), nullable=False)
    trait_id = Column(String(36), ForeignKey("traits.id", ondelete="SET NULL"), nullable=True)

    gap_score = Column(Float, nullable=False)  # G_o,t
    recommendation_type = Column(String(50), nullable=False)  # FOUNDATIONAL or REINFORCEMENT
    content = Column(JSON, nullable=False)  # { title, summary, key_concepts, reading_chunks, practice_items }
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("User")
    objective = relationship("CourseObjective")
    trait = relationship("Trait")
