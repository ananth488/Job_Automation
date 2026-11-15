"""Job Search and Automation Preferences API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, Preference
from app.schemas.preference import PreferenceResponse, PreferenceUpdate

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("/", response_model=PreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current job search and matching preferences."""
    pref = db.scalar(select(Preference).where(Preference.user_id == current_user.id))
    if not pref:
        pref = Preference(
            user_id=current_user.id,
            desired_roles=["Full Stack Developer", "Python Backend Engineer"],
            keywords=["Python", "FastAPI", "React", "Docker", "SQL"],
            locations=["Bengaluru", "Hyderabad", "Remote"],
            work_mode="any",
            match_threshold=80,
            daily_limit=20,
            approval_mode="below_threshold",
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("/", response_model=PreferenceResponse)
def update_preferences(
    pref_in: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update job search preferences and match criteria."""
    pref = db.scalar(select(Preference).where(Preference.user_id == current_user.id))
    if not pref:
        pref = Preference(user_id=current_user.id)
        db.add(pref)

    update_data = pref_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pref, field, value)

    pref.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pref)
    return pref

