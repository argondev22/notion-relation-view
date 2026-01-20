"""
Notion API router for token management and verification.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.routers.auth import get_current_user
from app.services.notion_client import notion_client, InvalidTokenError, NetworkError, NotionAPIError
from app.models.user import User
from app.models.notion_token import NotionToken
from app.services.auth_service import auth_service


router = APIRouter(prefix="/api/notion", tags=["notion"])


class SaveTokenRequest(BaseModel):
    """Request model for saving Notion token"""
    token: str


class TokenVerifyResponse(BaseModel):
    """Response model for token verification"""
    valid: bool
    workspace_name: str | None = None
    error: str | None = None


@router.post("/token", status_code=status.HTTP_200_OK)
async def save_notion_token(
    request: SaveTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save Notion API token for the current user.

    The token is encrypted before storage for security.

    Args:
        request: Request containing the Notion API token
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token validation or storage fails
    """
    try:
        # Verify the token is valid before saving
        auth_result = await notion_client.authenticate(request.token)

        if not auth_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Notion API token"
            )

        # Encrypt the token
        encrypted_token = auth_service.encrypt_notion_token(request.token)

        # Check if user already has a token
        existing_token = db.query(NotionToken).filter(
            NotionToken.user_id == current_user.id
        ).first()

        if existing_token:
            # Update existing token
            existing_token.encrypted_token = encrypted_token
        else:
            # Create new token entry
            new_token = NotionToken(
                user_id=current_user.id,
                encrypted_token=encrypted_token
            )
            db.add(new_token)

        db.commit()

        return {
            "message": "Notion token saved successfully",
            "workspace_name": auth_result.get("workspace_name")
        }

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Notion API token: {str(e)}"
        )
    except NetworkError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Network error while verifying token: {str(e)}"
        )
    except NotionAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying token: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save token: {str(e)}"
        )


@router.get("/token/verify", response_model=TokenVerifyResponse)
async def verify_notion_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify the stored Notion API token for the current user.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Token verification result with workspace name if valid

    Raises:
        HTTPException: If no token is stored or verification fails
    """
    try:
        # Get the stored token
        stored_token = db.query(NotionToken).filter(
            NotionToken.user_id == current_user.id
        ).first()

        if not stored_token:
            return TokenVerifyResponse(
                valid=False,
                error="No Notion token stored for this user"
            )

        # Decrypt the token
        decrypted_token = auth_service.decrypt_notion_token(stored_token.encrypted_token)

        # Verify the token with Notion API
        auth_result = await notion_client.authenticate(decrypted_token)

        if auth_result.get("success"):
            return TokenVerifyResponse(
                valid=True,
                workspace_name=auth_result.get("workspace_name")
            )
        else:
            return TokenVerifyResponse(
                valid=False,
                error="Token is no longer valid"
            )

    except InvalidTokenError:
        return TokenVerifyResponse(
            valid=False,
            error="Invalid Notion API token"
        )
    except NetworkError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Network error while verifying token: {str(e)}"
        )
    except NotionAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify token: {str(e)}"
        )
