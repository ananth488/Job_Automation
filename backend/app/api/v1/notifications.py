"""Notifications API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, Notification
from app.schemas.bot import NotificationResponse, NotificationListResponse, UnreadCountResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recent notifications."""
    notifs = db.scalars(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(50)
    ).all()

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifs],
        total=len(notifs),
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a specific notification as read."""
    notif = db.scalar(
        select(Notification).where(
            (Notification.id == notification_id) & (Notification.user_id == current_user.id)
        )
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.put("/read-all", response_model=dict)
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for current user."""
    notifs = db.scalars(
        select(Notification).where(
            (Notification.user_id == current_user.id) & (Notification.is_read == False)  # noqa: E712
        )
    ).all()

    for n in notifs:
        n.is_read = True
    db.commit()

    return {"message": f"Marked {len(notifs)} notifications as read"}


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get number of unread notifications."""
    count = db.scalar(
        select(func.count(Notification.id)).where(
            (Notification.user_id == current_user.id) & (Notification.is_read == False)  # noqa: E712
        )
    ) or 0
    return UnreadCountResponse(count=count)

