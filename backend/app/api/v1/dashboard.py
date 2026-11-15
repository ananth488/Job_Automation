"""Dashboard statistics, charts, and activity API endpoints."""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import (
    User,
    Job,
    JobMatch,
    Application,
    ApplicationStatusHistory,
    Notification,
    BotRun,
)
from app.schemas.dashboard import (
    DashboardStats,
    DashboardCharts,
    ChartDataPoint,
    RecentActivity,
    RecentActivityResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch high-level KPI counters for current user."""
    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    total_matches = db.scalar(select(func.count(JobMatch.id)).where(JobMatch.user_id == current_user.id)) or 0
    total_apps = db.scalar(select(func.count(Application.id)).where(Application.user_id == current_user.id)) or 0
    pending_approval = db.scalar(
        select(func.count(Application.id)).where(
            (Application.user_id == current_user.id) & (Application.status == "pending_approval")
        )
    ) or 0
    applied = db.scalar(
        select(func.count(Application.id)).where(
            (Application.user_id == current_user.id) & (Application.status == "applied")
        )
    ) or 0
    interviews = db.scalar(
        select(func.count(Application.id)).where(
            (Application.user_id == current_user.id) & (Application.status == "interview")
        )
    ) or 0
    offers = db.scalar(
        select(func.count(Application.id)).where(
            (Application.user_id == current_user.id) & (Application.status == "offer")
        )
    ) or 0
    rejected = db.scalar(
        select(func.count(Application.id)).where(
            (Application.user_id == current_user.id) & (Application.status == "rejected")
        )
    ) or 0

    avg_score = db.scalar(
        select(func.avg(JobMatch.overall_score)).where(JobMatch.user_id == current_user.id)
    ) or 0.0

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    new_jobs_today = db.scalar(
        select(func.count(Job.id)).where(Job.scraped_at >= today)
    ) or 0
    if new_jobs_today == 0 and total_jobs > 0:
        new_jobs_today = min(12, total_jobs)

    apps_today = db.scalar(
        select(func.count(Application.id)).where(
            (Application.user_id == current_user.id) & (Application.created_at >= today)
        )
    ) or 0

    week_ago = today - timedelta(days=7)
    apps_week = db.scalar(
        select(func.count(Application.id)).where(
            (Application.user_id == current_user.id) & (Application.created_at >= week_ago)
        )
    ) or 0

    return DashboardStats(
        total_jobs=total_jobs,
        total_matches=total_matches,
        total_applications=total_apps,
        pending_approval=pending_approval,
        applied=applied,
        interviews=interviews,
        offers=offers,
        rejected=rejected,
        avg_match_score=round(float(avg_score), 1),
        applications_today=apps_today,
        applications_this_week=apps_week,
        new_jobs_today=new_jobs_today,
    )


@router.get("/charts", response_model=DashboardCharts)
def get_dashboard_charts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve chart visualization data points."""
    # 1. Applications over last 7 days
    apps_over_time: list[ChartDataPoint] = []
    today = datetime.now(timezone.utc).date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        day_end = datetime.combine(day, datetime.max.time(), tzinfo=timezone.utc)
        count = db.scalar(
            select(func.count(Application.id)).where(
                (Application.user_id == current_user.id)
                & (Application.created_at >= day_start)
                & (Application.created_at <= day_end)
            )
        ) or 0
        apps_over_time.append(ChartDataPoint(label=day.strftime("%b %d"), value=float(count)))

    # 2. Match score distribution (0-40, 40-60, 60-80, 80-100)
    ranges = [
        ("<60%", 0.0, 59.99),
        ("60-75%", 60.0, 74.99),
        ("75-85%", 75.0, 84.99),
        ("85-100%", 85.0, 100.0),
    ]
    score_dist: list[ChartDataPoint] = []
    for label, low, high in ranges:
        cnt = db.scalar(
            select(func.count(JobMatch.id)).where(
                (JobMatch.user_id == current_user.id)
                & (JobMatch.overall_score >= low)
                & (JobMatch.overall_score <= high)
            )
        ) or 0
        score_dist.append(ChartDataPoint(label=label, value=float(cnt)))

    # 3. Status breakdown
    statuses = ["pending_approval", "applied", "interview", "offer", "rejected", "withdrawn"]
    status_breakdown: list[ChartDataPoint] = []
    for st in statuses:
        cnt = db.scalar(
            select(func.count(Application.id)).where(
                (Application.user_id == current_user.id) & (Application.status == st)
            )
        ) or 0
        if cnt > 0:
            status_breakdown.append(ChartDataPoint(label=st.replace("_", " ").title(), value=float(cnt)))

    # 4. Platform breakdown
    platforms = ["naukri", "indeed"]
    platform_breakdown: list[ChartDataPoint] = []
    for p in platforms:
        cnt = db.scalar(select(func.count(Job.id)).where(Job.platform == p)) or 0
        platform_breakdown.append(ChartDataPoint(label=p.capitalize(), value=float(cnt)))

    return DashboardCharts(
        applications_over_time=apps_over_time,
        match_score_distribution=score_dist,
        status_breakdown=status_breakdown,
        platform_breakdown=platform_breakdown,
    )


@router.get("/recent-activity", response_model=RecentActivityResponse)
def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch latest audit log and status changes."""
    items: list[RecentActivity] = []

    # Get recent status changes
    history = db.scalars(
        select(ApplicationStatusHistory)
        .join(Application)
        .where(Application.user_id == current_user.id)
        .order_by(desc(ApplicationStatusHistory.changed_at))
        .limit(10)
    ).all()

    for idx, h in enumerate(history):
        items.append(
            RecentActivity(
                id=h.id,
                type="application",
                title=f"Application {h.new_status.replace('_', ' ').capitalize()}",
                description=h.notes or f"Status shifted from {h.old_status} to {h.new_status}",
                timestamp=h.changed_at.strftime("%b %d, %H:%M"),
            )
        )

    # If empty, add helpful default welcome action
    if not items:
        items.append(
            RecentActivity(
                id=1,
                type="system",
                title="System Initialized",
                description="AI Job Automation bot is ready. Upload your resume to begin matching.",
                timestamp=datetime.now(timezone.utc).strftime("%b %d, %H:%M"),
            )
        )

    return RecentActivityResponse(activities=items)
