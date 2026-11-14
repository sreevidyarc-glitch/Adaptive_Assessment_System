import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    objectives = relationship("CourseObjective", back_populates="course", cascade="all, delete-orphan")
    faculty_assignments = relationship("FacultyAssignment", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="course", cascade="all, delete-orphan")
    materials = relationship("CourseMaterial", back_populates="course", cascade="all, delete-orphan")
    chunks = relationship("CourseMaterialChunk", back_populates="course", cascade="all, delete-orphan")

class CourseObjective(Base):
    __tablename__ = "course_objectives"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(20), nullable=False)  # e.g., "CO1", "CO2"
    description = Column(Text, nullable=False)
    weight = Column(Float, default=1.0)  # Priority weight w_o

    course = relationship("Course", back_populates="objectives")
    questions = relationship("Question", back_populates="objective")
    mapped_chunks = relationship("CourseMaterialChunk", back_populates="mapped_objective")

class FacultyAssignment(Base):
    __tablename__ = "faculty_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    faculty_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (UniqueConstraint("faculty_id", "course_id", name="uq_faculty_course"),)

    faculty = relationship("User", back_populates="faculty_assignments")
    course = relationship("Course", back_populates="faculty_assignments")

class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)

    course = relationship("Course", back_populates="materials")
    chunks = relationship("CourseMaterialChunk", back_populates="material", cascade="all, delete-orphan")

class CourseMaterialChunk(Base):
    """
    Stores module-wise paragraph/sentence chunks S as required by Section 3 lines 48-60.
    """
    __tablename__ = "course_material_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id = Column(String(36), ForeignKey("course_materials.id", ondelete="CASCADE"), nullable=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    module_name = Column(String(100), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    # Mapping to Learning Objectives
    mapped_objective_id = Column(String(36), ForeignKey("course_objectives.id", ondelete="SET NULL"), nullable=True)
    similarity_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    material = relationship("CourseMaterial", back_populates="chunks")
    course = relationship("Course", back_populates="chunks")
    mapped_objective = relationship("CourseObjective", back_populates="mapped_chunks")
