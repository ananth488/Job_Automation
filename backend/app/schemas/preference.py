"""Job preference Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class PreferenceUpdate(BaseModel):
    """Schema for creating or updating preferences."""

    desired_roles: list[str] | None = None
    keywords: list[str] | None = None
    locations: list[str] | None = None
    work_mode: str = "any"
    min_salary: int | None = None
    max_salary: int | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    notice_period: str | None = None
    preferred_companies: list[str] | None = None
    blocked_companies: list[str] | None = None
    job_types: list[str] | None = None
    match_threshold: int = Field(default=80, ge=0, le=100)
    daily_limit: int = Field(default=20, ge=1, le=100)
    posted_within_days: int | None = 30
    approval_mode: str = "below_threshold"


class PreferenceResponse(BaseModel):
    """Schema for preferences in API responses."""

    id: int
    user_id: int
    desired_roles: list[str] | None = None
    keywords: list[str] | None = None
    locations: list[str] | None = None
    work_mode: str
    min_salary: int | None = None
    max_salary: int | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    notice_period: str | None = None
    preferred_companies: list[str] | None = None
    blocked_companies: list[str] | None = None
    job_types: list[str] | None = None
    match_threshold: int
    daily_limit: int
    posted_within_days: int | None = 30
    approval_mode: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
