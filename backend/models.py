from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector
from database import Base
import uuid
import enum
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    candidate = "candidate"
    recruiter = "recruiter"


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    reviewed = "reviewed"
    rejected = "rejected"
    offered = "offered"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    candidate_profile = relationship("CandidateProfile", back_populates="user", uselist=False)
    posted_jobs = relationship("Job", back_populates="recruiter")
    applications = relationship("Application", back_populates="candidate")


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(Text, default="")
    skills = Column(ARRAY(String), default=[])
    experience = Column(Text, default="")  # JSON string of experience list
    education = Column(Text, default="")   # JSON string of education list
    resume_url = Column(String, default="")
    resume_text = Column(Text, default="")  # raw extracted text
    embedding = Column(Vector(384), nullable=True)  # all-MiniLM-L6-v2 dim
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="candidate_profile")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, default="Remote")
    description = Column(Text, nullable=False)
    requirements = Column(Text, default="")
    salary_range = Column(String, default="")
    job_type = Column(String, default="Full-time")  # Full-time, Part-time, Contract
    is_active = Column(Boolean, default=True)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    recruiter = relationship("User", back_populates="posted_jobs")
    applications = relationship("Application", back_populates="job")


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.applied)
    cover_note = Column(Text, default="")
    applied_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    candidate = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
