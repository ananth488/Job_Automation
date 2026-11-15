"""Notification service — creates and manages in-app notifications."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.models import Notification


class NotificationService:
    """Creates and manages user notifications."""

    def create_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
    ) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def create_approval_notification(
        self,
        db: Session,
        user_id: int,
        job_title: str,
        company: str,
        match_score: float,
    ) -> Notification:
        """Create an approval-needed notification."""
        return self.create_notification(
            db=db,
            user_id=user_id,
            notification_type="approval_needed",
            title=f"Approval needed: {job_title} at {company}",
            message=(
                f"A new job match ({match_score:.0f}% score) for {job_title} at {company} "
                f"requires your approval before applying."
            ),
        )

    def create_interview_alert(
        self,
        db: Session,
        user_id: int,
        job_title: str,
        company: str,
    ) -> Notification:
        """Create an interview alert notification."""
        return self.create_notification(
            db=db,
            user_id=user_id,
            notification_type="interview_alert",
            title=f"Interview: {job_title} at {company}",
            message=f"Great news! Your application for {job_title} at {company} has progressed to the interview stage.",
        )

    def create_daily_summary(
        self,
        db: Session,
        user_id: int,
        jobs_found: int,
        jobs_matched: int,
        applications: int,
    ) -> Notification:
        """Create a daily summary notification."""
        return self.create_notification(
            db=db,
            user_id=user_id,
            notification_type="daily_summary",
            title="Daily Bot Summary",
            message=(
                f"Today's results: {jobs_found} jobs found, {jobs_matched} matched, "
                f"{applications} applications submitted."
            ),
        )
