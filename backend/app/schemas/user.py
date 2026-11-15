"""User-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    full_name: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str  # OAuth2 form expects 'username'
    password: str


class UserResponse(BaseModel):
    """Schema for user in API responses."""

    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None


class TokenData(BaseModel):
    """Data embedded in the JWT token."""

    sub: int | None = None
