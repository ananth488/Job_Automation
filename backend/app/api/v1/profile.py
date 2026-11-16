"""Candidate Profile API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, CandidateProfile
from app.schemas.profile import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve verified candidate profile for current user with smart experience sanitization."""
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile:
        profile = CandidateProfile(
            user_id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # Auto-sanitize any historical work experiences where company and title were swapped or merged
    if profile.experience and isinstance(profile.experience, list):
        sanitized_exp = []
        needs_commit = False
        from app.services.resume_parser.parser import ResumeParser
        parser = ResumeParser()
        for item in profile.experience:
            if isinstance(item, dict):
                t = item.get("title", "") or ""
                c = item.get("company", "") or ""
                loc = item.get("location", "") or ""
                if "|" in t or (parser._score_company(t) > 0 and not c) or (parser._score_company(t) > parser._score_title(t) and parser._score_title(c) > 0):
                    new_t, new_c, new_loc = parser._classify_experience_header([t, c] if c else [t])
                    item = {
                        **item,
                        "title": new_t or t,
                        "company": new_c or c,
                        "location": new_loc or loc,
                    }
                    needs_commit = True
            sanitized_exp.append(item)
        if needs_commit:
            profile.experience = sanitized_exp
            db.commit()
            db.refresh(profile)

    return profile


@router.put("/", response_model=ProfileResponse)
def update_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile data."""
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)

    update_dict = profile_in.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(profile, field, val)

    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/verify", response_model=ProfileResponse)
def verify_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm and mark candidate profile as verified."""
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    profile.is_verified = True
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile

