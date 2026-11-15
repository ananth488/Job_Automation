"""Job and job match Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JobSearchRequest(BaseModel):
    """Schema for triggering a manual job search."""

    keywords: list[str] | None = None
    location: str | None = None
    platforms: list[str] | None = None  # naukri / indeed


class JobResponse(BaseModel):
    """Schema for a job posting in API responses."""

    id: int
    platform: str
    external_job_id: str
    url: str | None = None
    apply_type: str = "direct_1click"
    company_type: str | None = "startup"
    company_url: str | None = None
    title: str
    company: str
    location: str | None = None
    work_mode: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    description: str | None = None
    skills_required: list[str] | None = None
    posted_date: datetime | None = None
    scraped_at: datetime
    is_active: bool
    match_score: int | None = None
    is_applied: bool = False

    model_config = {"from_attributes": True}


class JobMatchResponse(BaseModel):
    """Schema for a job match in API responses."""

    id: int
    user_id: int
    job_id: int
    overall_score: float
    skills_score: float
    experience_score: float
    location_score: float
    salary_score: float
    role_fit_score: float
    matched_skills: list[str] | None = None
    missing_skills: list[str] | None = None
    explanation: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JobWithMatchResponse(BaseModel):
    """Job with its match info for the current user."""

    job: JobResponse
    match: JobMatchResponse | None = None


class JobStatsResponse(BaseModel):
    """Aggregated job statistics."""

    total_jobs: int = 0
    active_jobs: int = 0
    naukri_jobs: int = 0
    indeed_jobs: int = 0
    avg_match_score: float = 0.0
    jobs_above_threshold: int = 0


class JobListResponse(BaseModel):
    """Paginated job list response."""

    items: list[JobResponse]
    total: int
    page: int
    size: int
