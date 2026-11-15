"""Bot-related Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BotStatusResponse(BaseModel):
    """Current status of the bot."""

    is_running: bool = False
    status: str = "stopped"  # running/stopped/paused
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    current_run_id: int | None = None


class BotSettingsUpdate(BaseModel):
    """Schema for updating bot settings."""

    run_schedule: str | None = None
    naukri_enabled: bool = True
    indeed_enabled: bool = True


class BotSettingsResponse(BaseModel):
    """Schema for bot settings in API responses."""

    id: int
    user_id: int
    is_running: bool
    run_schedule: str | None = None
    naukri_enabled: bool
    indeed_enabled: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BotRunResponse(BaseModel):
    """Schema for bot run history entries."""

    id: int
    user_id: int
    started_at: datetime
    ended_at: datetime | None = None
    status: str
    jobs_found: int
    jobs_matched: int
    applications_submitted: int
    errors: list[str] | None = None
    log: str | None = None

    model_config = {"from_attributes": True}


class BotRunListResponse(BaseModel):
    """Paginated bot run list."""

    items: list[BotRunResponse]
    total: int


class NotificationResponse(BaseModel):
    """Schema for notifications."""

    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Paginated notification list."""

    items: list[NotificationResponse]
    total: int


class UnreadCountResponse(BaseModel):
    """Unread notification count."""

    count: int
