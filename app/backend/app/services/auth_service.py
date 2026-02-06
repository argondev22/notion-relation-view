"""
Authentication service for Google OIDC
"""

import secrets
import hashlib
import base64
import logging
import httpx
from typing import Dict, Optional, Any, TypedDict
from urllib.parse import urlencode
from jose import jwt, JWTError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


class TokenResponse(TypedDict):
    """Google OAuth token response structure"""

    id_token: str
    access_token: str
    expires_in: int
    token_type: str
    scope: str
    refresh_token: Optional[str]


class IDTokenPayload(TypedDict):
    """Decoded ID token payload structure"""

    iss: str  # Issuer
    sub: str  # Subject (user ID)
    aud: str  # Audience
    exp: int  # Expiration time
    iat: int  # Issued at
    email: str
    email_verified: bool
    name: str
    picture: Optional[str]


class AuthService:
    """Service for handling Google OIDC authentication"""

    GOOGLE_DISCOVERY_URL = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    HTTP_TIMEOUT = 10.0  # seconds

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self._discovery_cache: Optional[Dict[str, Any]] = None

    async def _get_discovery_document(self) -> Dict[str, Any]:
        """
        Fetch and cache Google's OIDC discovery document

        Returns:
            Discovery document containing OAuth endpoints

        Raises:
            HTTPException: If discovery document cannot be fetched
        """
        if self._discovery_cache:
            return self._discovery_cache

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                response = await client.get(self.GOOGLE_DISCOVERY_URL)
                response.raise_for_status()
                self._discovery_cache = response.json()
                return self._discovery_cache
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Failed to fetch discovery document: "
                    f"{e.response.status_code if e.response else 'unknown'} - "
                    f"{e.response.text if e.response else str(e)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service temporarily unavailable.",
                )
            except httpx.RequestError as e:
                logger.error(f"Failed to fetch discovery document: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service temporarily unavailable.",
                )

    async def get_authorization_endpoint(self) -> str:
        """
        Get authorization endpoint from discovery document

        Returns:
            Authorization endpoint URL

        Raises:
            HTTPException: If endpoint not found in discovery document
        """
        discovery = await self._get_discovery_document()
        endpoint = discovery.get("authorization_endpoint")
        if not endpoint:
            logger.error("Authorization endpoint not found in discovery document")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service configuration error.",
            )
        return endpoint

    async def get_token_endpoint(self) -> str:
        """
        Get token endpoint from discovery document

        Returns:
            Token endpoint URL

        Raises:
            HTTPException: If endpoint not found in discovery document
        """
        discovery = await self._get_discovery_document()
        endpoint = discovery.get("token_endpoint")
        if not endpoint:
            logger.error("Token endpoint not found in discovery document")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service configuration error.",
            )
        return endpoint

    async def get_jwks_uri(self) -> str:
        """
        Get JWKS URI from discovery document

        Returns:
            JWKS URI URL

        Raises:
            HTTPException: If URI not found in discovery document
        """
        discovery = await self._get_discovery_document()
        uri = discovery.get("jwks_uri")
        if not uri:
            logger.error("JWKS URI not found in discovery document")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service configuration error.",
            )
        return uri

    def generate_state(self) -> str:
        """
        Generate random state parameter for CSRF protection

        The state parameter is used to prevent CSRF attacks by ensuring
        that the authorization response corresponds to the request made
        by this application.

        Returns:
            Random state string (32 bytes URL-safe base64 encoded)

        Example:
            >>> auth_service = AuthService()
            >>> state = auth_service.generate_state()
            >>> len(state) >= 32
            True

        Note:
            Store this state in the user's session and verify it matches
            when handling the OAuth callback.
        """
        return secrets.token_urlsafe(32)

    def generate_code_verifier(self) -> str:
        """
        Generate PKCE code verifier

        PKCE (Proof Key for Code Exchange) adds an additional layer of
        security to the OAuth flow by preventing authorization code
        interception attacks.

        Returns:
            Random code verifier string (128 bytes URL-safe base64 encoded)

        Example:
            >>> auth_service = AuthService()
            >>> verifier = auth_service.generate_code_verifier()
            >>> len(verifier) >= 128
            True

        Note:
            Store this verifier securely (e.g., in session) as it will be
            needed during the token exchange step.

        See Also:
            - generate_code_challenge: Creates challenge from this verifier
            - RFC 7636: https://tools.ietf.org/html/rfc7636
        """
        return secrets.token_urlsafe(128)

    def generate_code_challenge(self, code_verifier: str) -> str:
        """
        Generate PKCE code challenge from verifier using S256 method

        Args:
            code_verifier: PKCE code verifier

        Returns:
            Code challenge string (base64url-encoded SHA256 hash)

        Example:
            >>> auth_service = AuthService()
            >>> verifier = auth_service.generate_code_verifier()
            >>> challenge = auth_service.generate_code_challenge(verifier)
            >>> challenge != verifier
            True

        Note:
            Uses S256 method as recommended by RFC 7636 for production use.
        """
        digest = hashlib.sha256(code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")

    async def get_google_login_url(self, state: str, code_challenge: str) -> str:
        """
        Generate Google OAuth login URL with PKCE

        Args:
            state: CSRF protection state parameter
            code_challenge: PKCE code challenge

        Returns:
            Google OAuth authorization URL

        Raises:
            HTTPException: If unable to fetch authorization endpoint
        """
        auth_endpoint = await self.get_authorization_endpoint()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        }

        query_string = urlencode(params)
        return f"{auth_endpoint}?{query_string}"

    async def exchange_code_for_token(
        self, code: str, code_verifier: str
    ) -> TokenResponse:
        """
        Exchange authorization code for ID token

        This method completes the OAuth flow by exchanging the authorization
        code received from Google for an ID token and access token.

        Args:
            code: Authorization code from Google OAuth callback
            code_verifier: PKCE code verifier generated earlier

        Returns:
            Token response containing:
                - id_token: JWT containing user identity information
                - access_token: Token for accessing Google APIs
                - expires_in: Token lifetime in seconds
                - token_type: Usually "Bearer"
                - scope: Granted OAuth scopes
                - refresh_token: Optional token for obtaining new access tokens

        Raises:
            HTTPException:
                - 401 UNAUTHORIZED: Invalid code or verification failed
                - 502 BAD_GATEWAY: Network error connecting to Google

        Example:
            >>> code = "4/0AX4XfWh..."
            >>> verifier = session.get("code_verifier")
            >>> tokens = await auth_service.exchange_code_for_token(code, verifier)
            >>> id_token = tokens["id_token"]

        Note:
            The authorization code can only be used once and expires quickly
            (typically within 10 minutes).
        """
        token_endpoint = await self.get_token_endpoint()

        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            try:
                response = await client.post(token_endpoint, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Log detailed error for debugging
                status_code = e.response.status_code if e.response else "unknown"
                response_text = e.response.text if e.response else str(e)
                logger.error(f"Token exchange failed: {status_code} - {response_text}")
                # Return generic error to user
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed. Please try again.",
                )
            except httpx.RequestError as e:
                # Log detailed error
                logger.error(f"Network error during token exchange: {str(e)}")
                # Return generic error to user
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to connect to authentication service.",
                )

    async def verify_id_token(self, id_token: str) -> IDTokenPayload:
        """
        Verify Google ID token and extract user information

        This method validates the ID token signature, issuer, audience,
        and expiration, then extracts the user information from the payload.

        Args:
            id_token: Google ID token (JWT)

        Returns:
            Decoded token payload with user info including:
                - email: User email address
                - name: User full name
                - picture: URL to user profile picture
                - sub: Google user ID
                - email_verified: Whether email is verified

        Raises:
            HTTPException:
                - 401 UNAUTHORIZED: Invalid token or verification failed
                - 502 BAD_GATEWAY: Network error fetching public keys

        Example:
            >>> id_token = tokens["id_token"]
            >>> payload = await auth_service.verify_id_token(id_token)
            >>> user_email = payload["email"]

        Note:
            This method fetches Google public keys to verify the token
            signature. The keys are cached by httpx for performance.
        """
        try:
            # Decode without verification first to get header
            unverified_header = jwt.get_unverified_header(id_token)

            # Fetch Google's public keys
            jwks_uri = await self.get_jwks_uri()
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                jwks_response = await client.get(jwks_uri)
                jwks_response.raise_for_status()
                jwks = jwks_response.json()

            # Find the key that matches the token's kid
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == unverified_header.get("kid"):
                    key = jwk
                    break

            if not key:
                logger.warning(f"Key ID not found: {unverified_header.get('kid')}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token.",
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
            logger.error(f"JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch JWKS: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to verify authentication token.",
            )

    def get_or_create_user(
        self, db: Session, email: str, name: str, picture: Optional[str] = None
    ) -> User:
        """
        Get existing user or create new user from Google info

        This method implements an idempotent user creation pattern,
        ensuring that users are created only once and updated if their
        information changes.

        Args:
            db: Database session
            email: User email from Google
            name: User name from Google
            picture: User profile picture URL from Google

        Returns:
            User model instance (either existing or newly created)

        Raises:
            HTTPException:
                - 500 INTERNAL_SERVER_ERROR: Database operation failed

        Example:
            >>> payload = await auth_service.verify_id_token(id_token)
            >>> user = auth_service.get_or_create_user(
            ...     db, payload["email"], payload["name"], payload.get("picture")
            ... )

        Note:
            This method handles race conditions where multiple requests
            might try to create the same user simultaneously.
        """
        try:
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

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error for email {email}: {str(e)}")
            # Race condition: user was created between check and insert
            # Try to fetch again
            user = db.query(User).filter(User.email == email).first()
            if user:
                return user
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account.",
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in get_or_create_user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed.",
            )
