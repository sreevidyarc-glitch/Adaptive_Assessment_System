import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Trait(Base):
    """Assessment traits (e.g. Conceptual Understanding, Problem Solving, Analytical Thinking)."""
    __tablename__ = "traits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    questions = relationship("Question", back_populates="trait")

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    objective_id = Column(String(36), ForeignKey("course_objectives.id", ondelete="CASCADE"), nullable=False)
    trait_id = Column(String(36), ForeignKey("traits.id", ondelete="SET NULL"), nullable=True)
    
    prompt = Column(Text, nullable=False)
    hint1 = Column(Text, nullable=True)
    hint2 = Column(Text, nullable=True)
    
    # Approval & Publication Status
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    is_published = Column(Boolean, default=False)
    
    # Validation & Retry Metadata
    generation_retries = Column(Integer, default=0)
    validation_status = Column(String(50), default="PASSED")  # PASSED or UNRESOLVED_FAILURE
    validation_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    course = relationship("Course", back_populates="questions")
    objective = relationship("CourseObjective", back_populates="questions")
    trait = relationship("Trait", back_populates="questions")
    
    # STRICT PRIVACY: Rubrics and Model Answers are isolated
    rubric = relationship("Rubric", uselist=False, back_populates="question", cascade="all, delete-orphan")
    model_answer = relationship("ModelAnswer", uselist=False, back_populates="question", cascade="all, delete-orphan")

class Rubric(Base):
    """
    CRITICAL: Visible to authorized faculty only.
    Never exposed to students in any student-facing endpoint.
    """
    __tablename__ = "rubrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_points = Column(Float, nullable=False, default=10.0)
    criteria = Column(JSON, nullable=False)  # Breakdown of criteria, performance levels, evidence weights w_i
    created_at = Column(DateTime(timezone=True), default=utcnow)

    question = relationship("Question", back_populates="rubric")

class ModelAnswer(Base):
    """
    CRITICAL: Visible to authorized faculty only.
    Never exposed to students in any student-facing endpoint.
    """
    __tablename__ = "model_answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    question = relationship("Question", back_populates="model_answer")

