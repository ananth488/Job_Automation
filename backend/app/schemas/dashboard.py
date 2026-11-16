"""Dashboard Pydantic schemas."""

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Overview counters for the dashboard."""

    total_jobs: int = 0
    total_matches: int = 0
    total_applications: int = 0
    pending_approval: int = 0
    applied: int = 0
    hr_shortlisted: int = 0
    interviews: int = 0
    offers: int = 0
    rejected: int = 0
    avg_match_score: float = 0.0
    applications_today: int = 0
    applications_this_week: int = 0
    new_jobs_today: int = 0


class ChartDataPoint(BaseModel):
    """A single data point for charts."""

    label: str
    value: float


class DashboardCharts(BaseModel):
    """Chart data for the dashboard."""

    applications_over_time: list[ChartDataPoint] = []
    match_score_distribution: list[ChartDataPoint] = []
    status_breakdown: list[ChartDataPoint] = []
    platform_breakdown: list[ChartDataPoint] = []


class RecentActivity(BaseModel):
    """A single recent activity entry."""

    id: int
    type: str
    title: str
    description: str
    timestamp: str


class RecentActivityResponse(BaseModel):
    """Recent activity list."""

    activities: list[RecentActivity] = []
