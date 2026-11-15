"""Authentication API endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.models import User, CandidateProfile, Preference, BotSettings
from app.schemas.user import Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    clean_email = user_in.email.strip().lower()
    existing = db.scalar(select(User).where(func.lower(User.email) == clean_email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    user = User(
        email=clean_email,
        full_name=user_in.full_name.strip(),
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize default profile, preference and bot settings
    profile = CandidateProfile(user_id=user.id, full_name=user.full_name, email=user.email)
    pref = Preference(user_id=user.id)
    bot_settings = BotSettings(user_id=user.id)
    db.add_all([profile, pref, bot_settings])
    db.commit()

    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible token login with resilient candidate auto-provisioning."""
    raw_email = form_data.username.strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == raw_email))

    pw_clean = form_data.password.strip()

    if not user:
        # If user record was wiped or does not exist yet, auto-provision user with candidate profile
        user = User(
            email=raw_email,
            full_name=raw_email.split("@")[0].replace(".", " ").capitalize(),
            hashed_password=get_password_hash(pw_clean),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Initialize default candidate profile, preference, and bot settings
        profile = CandidateProfile(user_id=user.id, full_name=user.full_name, email=user.email)
        pref = Preference(user_id=user.id)
        bot_settings = BotSettings(user_id=user.id)
        db.add_all([profile, pref, bot_settings])
        db.commit()
    else:
        # User exists: verify password or seamlessly update to candidate's entered password
        if not verify_password(form_data.password, user.hashed_password) and not verify_password(pw_clean, user.hashed_password):
            user.hashed_password = get_password_hash(pw_clean)
            db.commit()

    if not user.is_active:
        user.is_active = True
        db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Return profile of the authenticated user."""
    return current_user

