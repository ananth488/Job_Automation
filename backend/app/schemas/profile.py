"""Candidate profile Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    """Schema for creating or updating a candidate profile."""

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    preferred_locations: list[str] | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None
    skills: list[str] | None = None
    experience: list[dict[str, Any]] | None = None
    education: list[dict[str, Any]] | None = None
    certifications: list[str] | None = None
    projects: list[dict[str, Any]] | None = None
    total_experience_years: float | None = None


class ProfileResponse(BaseModel):
    """Schema for profile in API responses."""

    id: int
    user_id: int
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    preferred_locations: list[str] | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None
    skills: list[str] | None = None
    experience: list[dict[str, Any]] | None = None
    education: list[dict[str, Any]] | None = None
    certifications: list[str] | None = None
    projects: list[dict[str, Any]] | None = None
    total_experience_years: float | None = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
