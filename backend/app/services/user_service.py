"""User service — handles user CRUD, authentication, and default user creation."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.models import User


class UserService:
    """Service layer for user operations."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """Find a user by email address."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        """Find a user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, email: str, full_name: str, password: str) -> User:
        """Create a new user."""
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
