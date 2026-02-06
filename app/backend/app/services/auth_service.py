"""
Authentication service for Google OIDC
"""

import secrets
import httpx
import hashlib
import base64
from typing import Dict, Optional, Any
from jose import jwt, JWTError
from fastapi import HTTPException, status
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


REQUEST_TIMEOUT = 10.0


class AuthService:
    """Service for handling Google OIDC authentication"""

    GOOGLE_DISCOVERY_URL = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

    def generate_state(self) -> str:
        """
        Generate random state parameter for CSRF protection

        Returns:
            Random state string (32 bytes URL-safe)
        """
        return secrets.token_urlsafe(32)

    def generate_code_verifier(self) -> str:
        """
        Generate PKCE code verifier

        Returns:
            Random code verifier string (128 bytes URL-safe)
        """
        return secrets.token_urlsafe(128)

    def generate_code_challenge(self, code_verifier: str) -> str:
        """
        Generate PKCE code challenge from verifier
        Using plain method for simplicity (use S256 in production)

        Args:
            code_verifier: PKCE code verifier

        Returns:
            Code challenge string
        """
        digest = hashlib.sha256(code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")

    def get_google_login_url(self, state: str, code_challenge: str) -> str:
        """
        Generate Google OAuth login URL with PKCE

        Args:
            state: CSRF protection state parameter
            code_challenge: PKCE code challenge

        Returns:
            Google OAuth authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "plain",  # Use S256 in production
            "access_type": "offline",
            "prompt": "consent",
        }
        query_string = urlencode(params)
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"

    async def exchange_code_for_token(
        self, code: str, code_verifier: str
    ) -> Dict[str, str]:
        """
        Exchange authorization code for ID token

        Args:
            code: Authorization code from Google
            code_verifier: PKCE code verifier

        Returns:
            Token response containing id_token, access_token, etc.

        Raises:
            HTTPException: If token exchange fails
        """
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.post(self.GOOGLE_TOKEN_URL, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to exchange code for token: {e.response.text}",
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Network error during token exchange: {str(e)}",
                )

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Google ID token and extract user information

        Args:
            id_token: Google ID token (JWT)

        Returns:
            Decoded token payload with user info

        Raises:
            HTTPException: If token verification fails
        """
        try:
            # Decode without verification first to get header
            unverified_header = jwt.get_unverified_header(id_token)

            # Fetch Google's public keys
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                jwks_response = await client.get(self.GOOGLE_JWKS_URL)
                jwks_response.raise_for_status()
                jwks = jwks_response.json()

            # Find the key that matches the token's kid
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == unverified_header.get("kid"):
                    key = jwk
                    break

            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find appropriate key for token verification",
                )

            # Verify and decode the token
            payload = jwt.decode(
                id_token,
                key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer="https://accounts.google.com",
                options={"verify_exp": True},
            )

            return payload

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid ID token: {str(e)}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch Google public keys: {str(e)}",
            )

    def get_or_create_user(
        self, db: Session, email: str, name: str, picture: Optional[str] = None
    ) -> User:
        """
        Get existing user or create new user from Google info

        Args:
            db: Database session
            email: User email from Google
            name: User name from Google
            picture: User profile picture URL from Google

        Returns:
            User model instance
        """
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        if user:
            # Update user info if changed
            if user.name != name or user.picture != picture:
                user.name = name
                user.picture = picture
                db.commit()
                db.refresh(user)
            return user

        # Create new user
        user = User(email=email, name=name, picture=picture, plan="free")
        db.add(user)
        db.commit()
        db.refresh(user)

        return user
