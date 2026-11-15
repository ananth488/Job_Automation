"""Job discovery, filtering, and matching API endpoints."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, Job, JobMatch, CandidateProfile, Application, Preference
from app.schemas.job import (
    JobListResponse,
    JobResponse,
    JobWithMatchResponse,
    JobMatchResponse,
    JobSearchRequest,
    JobStatsResponse,
)
from app.workers.scheduler import run_job_search_cycle

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobListResponse)
def list_jobs(
    platform: str | None = None,
    work_mode: str | None = None,
    search: str | None = None,
    company_type: str | None = None,
    posted_within_days: int | None = Query(default=None, ge=0, le=180),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List jobs with optional platform, query, company type, and posted within days filters."""
    query = select(Job).where(Job.is_active == True)  # noqa: E712

    if platform:
        query = query.where(Job.platform == platform.lower())
    if work_mode and work_mode.lower() != "any":
        query = query.where(Job.work_mode == work_mode.lower())
    if company_type and company_type.lower() != "all":
        query = query.where(Job.company_type == company_type.lower())

    # Filter by job freshness (posted_within_days: 1, 3, 5, 10, 15, 30 days)
    effective_days = posted_within_days
    if effective_days is None:
        user_pref = db.scalar(select(Preference).where(Preference.user_id == current_user.id))
        if user_pref and user_pref.posted_within_days:
            effective_days = user_pref.posted_within_days

    if effective_days is not None and effective_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=int(effective_days))
        query = query.where(or_(Job.posted_date >= cutoff, Job.scraped_at >= cutoff))

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Job.title.ilike(search_pattern),
                Job.company.ilike(search_pattern),
                Job.description.ilike(search_pattern),
            )
        )

    # Count total
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    # Paginate
    offset = (page - 1) * size
    query = query.order_by(desc(Job.scraped_at)).offset(offset).limit(size)
    jobs = db.scalars(query).all()

    # Pre-fetch applied job IDs for current user
    applied_job_ids = set(
        db.scalars(
            select(Application.job_id).where(Application.user_id == current_user.id)
        ).all()
    )

    # Pre-fetch user job matches
    matches = {
        m.job_id: int(m.overall_score)
        for m in db.scalars(
            select(JobMatch).where(JobMatch.user_id == current_user.id)
        ).all()
        if m.overall_score is not None
    }

    items = []
    for j in jobs:
        resp = JobResponse.model_validate(j)
        resp.match_score = matches.get(j.id)
        resp.is_applied = j.id in applied_job_ids
        items.append(resp)

    return JobListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/stats", response_model=JobStatsResponse)
def get_job_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get aggregated job statistics."""
    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    active_jobs = db.scalar(select(func.count(Job.id)).where(Job.is_active == True)) or 0  # noqa: E712
    naukri_jobs = db.scalar(select(func.count(Job.id)).where(Job.platform == "naukri")) or 0
    indeed_jobs = db.scalar(select(func.count(Job.id)).where(Job.platform == "indeed")) or 0
    
    avg_score = db.scalar(
        select(func.avg(JobMatch.overall_score)).where(JobMatch.user_id == current_user.id)
    ) or 0.0

    above_threshold = db.scalar(
        select(func.count(JobMatch.id)).where(
            (JobMatch.user_id == current_user.id) & (JobMatch.overall_score >= 80.0)
        )
    ) or 0

    return JobStatsResponse(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        naukri_jobs=naukri_jobs,
        indeed_jobs=indeed_jobs,
        avg_match_score=round(float(avg_score), 1),
        jobs_above_threshold=above_threshold,
    )


@router.get("/{job_id}", response_model=JobWithMatchResponse)
def get_job_details(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed job description and match breakdown for current user."""
    job = db.scalar(select(Job).where(Job.id == job_id))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    match = db.scalar(
        select(JobMatch).where((JobMatch.job_id == job_id) & (JobMatch.user_id == current_user.id))
    )

    return JobWithMatchResponse(
        job=JobResponse.model_validate(job),
        match=JobMatchResponse.model_validate(match) if match else None,
    )


@router.post("/search")
async def trigger_job_search(
    request: JobSearchRequest | None = None,
    current_user: User = Depends(get_current_user),
):
    """Trigger on-demand job search across configured platforms."""
    result = await run_job_search_cycle(user_id=current_user.id)
    return {"message": "Job search completed", "result": result}

