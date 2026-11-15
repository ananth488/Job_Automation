"""Bot controls, status, and execution history API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, BotSettings, BotRun, CandidateProfile
from app.schemas.bot import (
    BotStatusResponse,
    BotSettingsResponse,
    BotSettingsUpdate,
    BotRunResponse,
    BotRunListResponse,
)
from app.workers.scheduler import run_job_search_cycle, start_scheduler, stop_scheduler

router = APIRouter(prefix="/bot", tags=["bot"])


@router.get("/status", response_model=BotStatusResponse)
def get_bot_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current operating status and next scheduled execution."""
    settings = db.scalar(select(BotSettings).where(BotSettings.user_id == current_user.id))
    if not settings:
        settings = BotSettings(user_id=current_user.id, is_running=False)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    latest_run = db.scalar(
        select(BotRun)
        .where(BotRun.user_id == current_user.id)
        .order_by(desc(BotRun.started_at))
    )

    bot_status = "stopped"
    if settings.is_running:
        # Check if there's an actively executing cycle right now
        if latest_run and latest_run.status == "running":
            bot_status = "executing"
        else:
            bot_status = "active"

    return BotStatusResponse(
        is_running=settings.is_running,
        status=bot_status,
        last_run_at=settings.last_run_at or (latest_run.started_at if latest_run else None),
        next_run_at=settings.next_run_at,
        current_run_id=latest_run.id if latest_run and latest_run.status == "running" else None,
    )


@router.post("/start", response_model=BotStatusResponse)
def start_bot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start automated job search cycles."""
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile or not profile.is_verified or not profile.skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile incomplete. Please upload your master resume in 'Resume & Profile' and click 'Save & Confirm Verification' before starting the bot.",
        )

    settings = db.scalar(select(BotSettings).where(BotSettings.user_id == current_user.id))
    if not settings:
        settings = BotSettings(user_id=current_user.id)
        db.add(settings)

    settings.is_running = True
    settings.updated_at = datetime.now(timezone.utc)
    db.commit()

    start_scheduler()

    return BotStatusResponse(
        is_running=True,
        status="running",
        last_run_at=settings.last_run_at,
        next_run_at=settings.next_run_at,
    )


@router.post("/pause", response_model=BotStatusResponse)
def pause_bot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pause bot cycles temporarily."""
    settings = db.scalar(select(BotSettings).where(BotSettings.user_id == current_user.id))
    if settings:
        settings.is_running = False
        settings.updated_at = datetime.now(timezone.utc)
        db.commit()

    return BotStatusResponse(
        is_running=False,
        status="paused",
        last_run_at=settings.last_run_at if settings else None,
    )


@router.post("/stop", response_model=BotStatusResponse)
def stop_bot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stop bot execution and background scheduler."""
    settings = db.scalar(select(BotSettings).where(BotSettings.user_id == current_user.id))
    if settings:
        settings.is_running = False
        settings.updated_at = datetime.now(timezone.utc)
        db.commit()

    stop_scheduler()

    return BotStatusResponse(
        is_running=False,
        status="stopped",
        last_run_at=settings.last_run_at if settings else None,
    )


@router.post("/run-now")
async def run_now(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger an immediate execution run."""
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile or not profile.is_verified or not profile.skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile incomplete. Please upload your master resume in 'Resume & Profile' and click 'Save & Confirm Verification' before running the bot.",
        )

    result = await run_job_search_cycle(user_id=current_user.id)
    settings = db.scalar(select(BotSettings).where(BotSettings.user_id == current_user.id))
    if settings:
        settings.last_run_at = datetime.now(timezone.utc)
        db.commit()
    return {"message": "Run completed successfully", "details": result}


@router.get("/settings", response_model=BotSettingsResponse)
def get_bot_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get bot schedule and platform enablement settings."""
    settings = db.scalar(select(BotSettings).where(BotSettings.user_id == current_user.id))
    if not settings:
        settings = BotSettings(
            user_id=current_user.id,
            is_running=False,
            run_schedule="0 */6 * * *",
            naukri_enabled=True,
            indeed_enabled=True,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("/settings", response_model=BotSettingsResponse)
def update_bot_settings(
    settings_in: BotSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update bot schedule and platform enablement toggles."""
    settings = db.scalar(select(BotSettings).where(BotSettings.user_id == current_user.id))
    if not settings:
        settings = BotSettings(user_id=current_user.id)
        db.add(settings)

    update_dict = settings_in.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(settings, field, val)

    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/runs", response_model=BotRunListResponse)
def list_bot_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List execution logs and history."""
    runs = db.scalars(
        select(BotRun)
        .where(BotRun.user_id == current_user.id)
        .order_by(desc(BotRun.started_at))
        .limit(20)
    ).all()

    return BotRunListResponse(
        items=[BotRunResponse.model_validate(r) for r in runs],
        total=len(runs),
    )

