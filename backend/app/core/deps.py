"""FastAPI dependencies for authentication and database access."""

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token_header: str | None = Depends(oauth2_scheme),
    token_query: str | None = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: extract and validate the current user from JWT in Authorization header or query param."""
    token = token_header or token_query
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception

    user = None
    # 1. Try resolving by integer user ID
    try:
        user_id_int = int(sub)
        user = db.query(User).filter(User.id == user_id_int).first()
    except (ValueError, TypeError):
        user = None

    # 2. If not resolved by ID, resolve by email
    if not user:
        user = db.query(User).filter(User.email == str(sub).strip().lower()).first()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user
