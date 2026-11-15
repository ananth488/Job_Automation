"""All SQLAlchemy ORM models for the Job Automation system."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """Registered user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    resumes: Mapped[list["Resume"]] = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    profile: Mapped["CandidateProfile | None"] = relationship(
        "CandidateProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    preferences: Mapped["Preference | None"] = relationship(
        "Preference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    matches: Mapped[list["JobMatch"]] = relationship("JobMatch", back_populates="user", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="user", cascade="all, delete-orphan"
    )
    common_answers: Mapped[list["CommonAnswer"]] = relationship(
        "CommonAnswer", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    bot_runs: Mapped[list["BotRun"]] = relationship("BotRun", back_populates="user", cascade="all, delete-orphan")
    bot_settings: Mapped["BotSettings | None"] = relationship(
        "BotSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Resume(Base):
    """Uploaded resume file with parsed data."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf / docx
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="resumes")


class CandidateProfile(Base):
    """Verified candidate profile assembled from parsed resumes."""

    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Current Location
    preferred_locations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # Preferred Locations
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    experience: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    education: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    certifications: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    projects: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    total_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="profile")


class Preference(Base):
    """User job-search preferences and automation rules."""

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    desired_roles: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    locations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    work_mode: Mapped[str] = mapped_column(String(20), default="any")  # remote/hybrid/onsite/any
    min_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notice_period: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_companies: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    blocked_companies: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    job_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # full-time, contract, etc.
    match_threshold: Mapped[int] = mapped_column(Integer, default=80)
    daily_limit: Mapped[int] = mapped_column(Integer, default=20)
    posted_within_days: Mapped[int] = mapped_column(Integer, default=30, nullable=True)
    approval_mode: Mapped[str] = mapped_column(String(20), default="below_threshold")  # always/below_threshold/auto
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="preferences")


class Job(Base):
    """Scraped job posting from external platforms."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # naukri / indeed
    external_job_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    apply_type: Mapped[str] = mapped_column(String(50), default="direct_1click", nullable=True)  # 'direct_1click' or 'company_portal'
    company_type: Mapped[str | None] = mapped_column(String(50), default="startup", nullable=True)  # 'startup', 'mid_sized', 'saas', 'mnc'
    company_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    work_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_required: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    posted_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("platform", "external_job_id", name="uq_platform_job"),)

    matches: Mapped[list["JobMatch"]] = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="job", cascade="all, delete-orphan"
    )


class JobMatch(Base):
    """Computed match between a user profile and a job posting."""

    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    skills_score: Mapped[float] = mapped_column(Float, default=0.0)
    experience_score: Mapped[float] = mapped_column(Float, default=0.0)
    location_score: Mapped[float] = mapped_column(Float, default=0.0)
    salary_score: Mapped[float] = mapped_column(Float, default=0.0)
    role_fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    matched_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="shortlisted")  # shortlisted/rejected/applied/skipped
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="matches")
    job: Mapped["Job"] = relationship("Job", back_populates="matches")
    application: Mapped["Application | None"] = relationship(
        "Application", back_populates="match", uselist=False
    )


class Application(Base):
    """Job application record."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    match_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("job_matches.id"), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="pending_approval"
    )  # pending_approval/approved/applied/viewed/rejected/interview/offer/withdrawn
    method: Mapped[str] = mapped_column(String(10), default="auto")  # auto / manual
    tailored_resume_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_letter_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="applications")
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    match: Mapped["JobMatch | None"] = relationship("JobMatch", back_populates="application")
    status_history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        "ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan"
    )
    documents: Mapped[list["GeneratedDocument"]] = relationship(
        "GeneratedDocument", back_populates="application", cascade="all, delete-orphan"
    )
    screening_answers: Mapped[list["ScreeningAnswer"]] = relationship(
        "ScreeningAnswer", back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationStatusHistory(Base):
    """Audit log for application status changes."""

    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="status_history")


class GeneratedDocument(Base):
    """AI-generated resume or cover letter for an application."""

    __tablename__ = "generated_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(20), nullable=False)  # resume / cover_letter
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    application: Mapped["Application"] = relationship("Application", back_populates="documents")


class ScreeningAnswer(Base):
    """Auto-generated answer to a screening question."""

    __tablename__ = "screening_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    application: Mapped["Application"] = relationship("Application", back_populates="screening_answers")


class CommonAnswer(Base):
    """User-defined common answers for recurring screening questions."""

    __tablename__ = "common_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    question_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # notice_period/ctc/authorization/relocation/etc
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="common_answers")


class Notification(Base):
    """In-app notification for the user."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # daily_summary/interview_alert/approval_needed
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class BotRun(Base):
    """Record of a single bot execution run."""

    __tablename__ = "bot_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running/completed/failed/paused
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_matched: Mapped[int] = mapped_column(Integer, default=0)
    applications_submitted: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    log: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="bot_runs")


class BotSettings(Base):
    """Per-user bot configuration and scheduling."""

    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    run_schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)  # cron string
    naukri_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    indeed_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    naukri_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    indeed_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    naukri_account_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    indeed_account_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="bot_settings")
