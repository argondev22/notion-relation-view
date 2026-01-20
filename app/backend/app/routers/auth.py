"""
Authentication router for user registration, login, logout, and session management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.services.auth_service import auth_service
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    AuthResponse,
    LoginResponse,
    LogoutResponse,
    UserResponse
)
from app.models.user import User


router = APIRouter(prefix="/api/auth", tags=["authentication"])


def get_current_user(
    db: Session = Depends(get_db),
    session_token: Optional[str] = Cookie(None, alias="session_token")
) -> User:
    """
    Dependency to get the current authenticated user from session token cookie.

    Args:
        db: Database session
        session_token: JWT session token from cookie

    Returns:
        Current authenticated User object

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        # Validate session token
        user_info = auth_service.validate_session(session_token)
        user_id_str = user_info["user_id"]

        # Convert string UUID to UUID object for PostgreSQL, keep as string for SQLite
        try:
            user_id = UUID(user_id_str)
        except (ValueError, AttributeError):
            user_id = user_id_str

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password.

    Args:
        request: User registration request with email and password
        db: Database session

    Returns:
        AuthResponse with success status and user information

    Raises:
        HTTPException: If user already exists or registration fails
    """
    try:
        # Register the user
        user = auth_service.register(db, request.email, request.password)

        return AuthResponse(
            success=True,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and create session with JWT token in HTTPOnly cookie.

    Args:
        request: User login request with email and password
        response: FastAPI response object to set cookie
        db: Database session

    Returns:
        LoginResponse with success status, token, and user information

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Authenticate user and get token
        session_data = auth_service.login(db, request.email, request.password)

        # Get user information
        user = db.query(User).filter(User.email == request.email).first()

        # Set HTTPOnly cookie with session token
        response.set_cookie(
            key="session_token",
            value=session_data["token"],
            httponly=True,
            secure=True,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24  # 24 hours
        )

        return LoginResponse(
            success=True,
            token=session_data["token"],
            expires_at=session_data["expires_at"],
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user by invalidating session token cookie.

    Args:
        response: FastAPI response object to clear cookie
        current_user: Current authenticated user (from dependency)

    Returns:
        LogoutResponse with success status and message
    """
    # Clear the session token cookie
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return LogoutResponse(
        success=True,
        message="Successfully logged out"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user (from dependency)

    Returns:
        UserResponse with user information
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )
