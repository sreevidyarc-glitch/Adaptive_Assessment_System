import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

class RoleEnum(str, enum.Enum):
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    roll_number = Column(String(50), unique=True, index=True, nullable=True)  # For students
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    department = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    otp_tokens = relationship("OTPToken", back_populates="user", cascade="all, delete-orphan")
    faculty_assignments = relationship("FacultyAssignment", back_populates="faculty")
    enrollments = relationship("CourseEnrollment", back_populates="student")
    mastery_scores = relationship("MasteryScore", back_populates="student")

class OTPToken(Base):
    __tablename__ = "otp_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    otp_code = Column(String(10), nullable=False)
    purpose = Column(String(50), default="FACULTY_LOGIN")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, default=0)
    is_consumed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="otp_tokens")

class TokenBlacklist(Base):
    """Stores invalidated JWT identifiers (jti) upon logout."""
    __tablename__ = "token_blacklist"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    jti = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    revoked_at = Column(DateTime(timezone=True), default=utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)

