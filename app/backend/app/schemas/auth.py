"""
Authentication schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator


class GoogleLoginResponse(BaseModel):
    """Response containing Google OIDC login URL"""

    auth_url: str = Field(..., description="Google authentication URL", min_length=1)


class GoogleCallbackRequest(BaseModel):
    """Request body for Google OIDC callback"""

    code: str = Field(
        ..., description="Authorization code from Google", min_length=1, max_length=2048
    )
    state: str = Field(
        ..., description="CSRF protection state parameter", min_length=1, max_length=256
    )


class UserResponse(BaseModel):
    """User information response"""

    id: str = Field(..., description="Unique user identifier", min_length=1)
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's display name", min_length=1, max_length=255)
    picture: str | None = Field(None, description="URL to user's profile picture", max_length=2048)
    plan: str = Field(
        default="free", description="User's subscription plan", pattern="^(free|pro)$"
    )

    class Config:
        from_attributes = True

    @validator("picture")
    def validate_picture_url(cls, v):
        """Validate picture url format"""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("Picture URL must start with http:// or https://")
        return v


class AuthResponse(BaseModel):
    """Authentication response with user info"""

    success: bool = Field(..., description="Whether authentication was successful")
    user: UserResponse | None = Field(
        None, description="User information (only present on success)"
    )
    error: str | None = Field(
        None, description="Error message (only present on failure)", max_length=500
    )

    @validator("user", always=True)
    def validate_user_on_success(cls, v, values):
        """Ensure user is present when success is True"""
        if values.get("success") and v is None:
            raise ValueError("User must be present when success is True")
        return v

    @validator("error", always=True)
    def validate_error_on_failure(cls, v, values):
        """Ensure error is present when success is False"""
        if not values.get("success") and not v:
            raise ValueError("Error message must be present when success is False")
        return v


class LogoutResponse(BaseModel):
    """Logout response"""

    success: bool = Field(..., description="Whether logout was successful")
    message: str = Field(..., description="Logout status message", min_length=1, max_length=200)
