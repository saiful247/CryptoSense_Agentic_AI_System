from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8,
                          description="Password must be at least 8 characters")


class UserResponse(BaseModel):
    """Schema for user data responses (excluding sensitive info)."""
    email: EmailStr
    user_id: str


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str
    user_id: str


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8,
                              description="Password must be at least 8 characters")


class TokenData(BaseModel):
    """Schema for token payload."""
    email: str = None


class UserLogin(BaseModel):
    """Schema for login requests."""
    email: EmailStr
    password: str
