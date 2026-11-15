"""Application-related Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ApplicationResponse(BaseModel):
    """Schema for an application in API responses."""

    id: int
    user_id: int
    job_id: int
    match_id: int | None = None
    status: str
    method: str
    tailored_resume_path: str | None = None
    cover_letter_path: str | None = None
    submitted_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    # Attached job & match details for frontend tracking
    job_title: str | None = None
    company: str | None = None
    location: str | None = None
    platform: str | None = None
    url: str | None = None
    work_mode: str | None = None
    score: int | None = None

    model_config = {"from_attributes": True}


class BulkApplyRequest(BaseModel):
    """Schema for bulk applying to multiple jobs at once."""

    job_ids: list[int]
    auto_approve: bool = True


class BulkApproveRequest(BaseModel):
    """Schema for bulk approving queued applications."""

    application_ids: list[int]


class ApplicationDetailResponse(BaseModel):
    """Application with related job, match, and documents."""

    application: ApplicationResponse
    job: dict[str, Any] | None = None
    match: dict[str, Any] | None = None
    documents: list[dict[str, Any]] = []
    screening_answers: list[dict[str, Any]] = []
    status_history: list[dict[str, Any]] = []


class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status."""

    status: str
    notes: str | None = None


class ApplicationListResponse(BaseModel):
    """Paginated application list."""

    items: list[ApplicationResponse]
    total: int
    page: int = 1
    size: int = 50


class GeneratedDocumentResponse(BaseModel):
    """Schema for a generated document."""

    id: int
    application_id: int
    doc_type: str
    file_path: str | None = None
    content_text: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScreeningAnswerResponse(BaseModel):
    """Schema for a screening answer."""

    id: int
    application_id: int
    question: str
    answer: str
    confidence_score: float
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}
