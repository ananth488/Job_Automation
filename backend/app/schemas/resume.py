"""Resume-related Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ParsedResumeData(BaseModel):
    """Structured data extracted from a resume."""

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[str] = []
    experience: list[dict[str, Any]] = []
    education: list[dict[str, Any]] = []
    certifications: list[str] = []
    projects: list[dict[str, Any]] = []
    total_experience_years: float | None = None


class ResumeResponse(BaseModel):
    """Schema for resume in API responses."""

    id: int
    user_id: int
    filename: str
    file_type: str
    raw_text: str | None = None
    parsed_data: dict[str, Any] | None = None
    is_verified: bool
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    """Schema for listing resumes (without raw_text)."""

    id: int
    filename: str
    file_type: str
    is_verified: bool
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}
