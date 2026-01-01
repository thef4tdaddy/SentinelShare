import logging
import os
import secrets
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlmodel import Session
from starlette.responses import JSONResponse, RedirectResponse

from backend.auth_utils import (
    authenticate_user,
    create_user,
    get_current_user,
    get_current_user_optional,
    get_or_create_legacy_user,
)
from backend.database import get_session
from backend.models import User
from backend.services.oauth2_service import OAuth2Service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str | None = None  # For new multi-user auth
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    forwarding_target_email: EmailStr | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    forwarding_target_email: str | None


@router.post("/login")
def login(
    request: Request, login_data: LoginRequest, session: Session = Depends(get_session)
):
    """
    Login endpoint supporting both legacy single-password mode and new multi-user mode.
    
    - If username is provided, use multi-user authentication
    - Otherwise, fall back to legacy DASHBOARD_PASSWORD mode
    """
    # Try multi-user authentication first if username is provided
    if login_data.username:
        user = authenticate_user(session, login_data.username, login_data.password)
        if user:
            request.session["authenticated"] = True
            request.session["user_id"] = user.id
            return {
                "status": "success",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin,
                },
            }
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Legacy mode: check against DASHBOARD_PASSWORD
    expected_password = os.environ.get("DASHBOARD_PASSWORD")
    if not expected_password:
        # If no DASHBOARD_PASSWORD and no username, require multi-user auth
        raise HTTPException(
            status_code=400,
            detail="Username required. Please use multi-user authentication.",
        )
    
    if login_data.password == expected_password:
        # In legacy mode, get or create an admin user
        legacy_user = get_or_create_legacy_user(session)
        if legacy_user:
            request.session["authenticated"] = True
            request.session["user_id"] = legacy_user.id
            return {
                "status": "success",
                "user": {
                    "id": legacy_user.id,
                    "username": legacy_user.username,
                    "email": legacy_user.email,
                    "is_admin": legacy_user.is_admin,
                },
            }
        else:
            # Legacy mode without user records
            request.session["authenticated"] = True
            return {"status": "success"}
    
    raise HTTPException(status_code=401, detail="Invalid password")


@router.post("/register", response_model=UserResponse)
def register(
    register_data: RegisterRequest,
    session: Session = Depends(get_session),
):
    """
    Register a new user.
    
    Note: In production, you may want to restrict registration or require admin approval.
    Set ALLOW_REGISTRATION=false in environment to disable this endpoint.
    """
    # Check if registration is allowed
    if os.environ.get("ALLOW_REGISTRATION", "true").lower() == "false":
        raise HTTPException(status_code=403, detail="Registration is disabled")
    
    try:
        user = create_user(
            session=session,
            username=register_data.username,
            email=register_data.email,
            password=register_data.password,
            is_admin=False,  # New users are not admins by default
            forwarding_target_email=register_data.forwarding_target_email,
        )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_admin=user.is_admin,
            forwarding_target_email=user.forwarding_target_email,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "logged_out"}


@router.get("/me")
def check_auth(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Check authentication status and return current user info.
    Supports both legacy mode and multi-user mode.
    """
    # Multi-user mode: return user info
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "is_admin": current_user.is_admin,
                "forwarding_target_email": current_user.forwarding_target_email,
            },
        }
    
    # Legacy mode: check old session flag
    if request.session.get("authenticated"):
        return {"authenticated": True, "legacy_mode": True}
    
    # No-auth dev mode
    if not os.environ.get("DASHBOARD_PASSWORD"):
        return {"authenticated": True, "dev_mode": True}
    
    raise HTTPException(status_code=401, detail="Not authenticated")


# OAuth2 Endpoints


@router.get("/{provider}/authorize")
def oauth2_authorize(request: Request, provider: str):
    """
    Initiate OAuth2 authorization flow for a provider.
    Redirects user to the provider's consent screen.
    """
    # Validate provider
    if provider.lower() not in ["google", "microsoft"]:
        raise HTTPException(status_code=400, detail="Unsupported OAuth2 provider")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session["oauth2_state"] = state
    request.session["oauth2_provider"] = provider.lower()

    # Get base URL from request
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/{provider.lower()}/callback"

    try:
        auth_url = OAuth2Service.get_authorization_url(
            provider.lower(), redirect_uri, state
        )
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider}/callback")
async def oauth2_callback(
    request: Request,
    provider: str,
    code: str,
    state: str,
    error: str | None = None,
    session: Session = Depends(get_session),
):
    """
    Handle OAuth2 callback from provider.
    Exchanges code for tokens and stores them in the database.
    """
    # Check for errors from OAuth provider
    if error:
        raise HTTPException(
            status_code=400, detail=f"OAuth2 authorization failed: {error}"
        )

    # Verify state to prevent CSRF attacks
    session_state = request.session.get("oauth2_state")
    session_provider = request.session.get("oauth2_provider")

    if not session_state or session_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    if session_provider != provider.lower():
        raise HTTPException(status_code=400, detail="Provider mismatch")

    # Clear OAuth session data
    request.session.pop("oauth2_state", None)
    request.session.pop("oauth2_provider", None)

    # Get base URL from request
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/auth/{provider.lower()}/callback"

    # Get current user ID from session (if authenticated)
    user_id = request.session.get("user_id")

    try:
        # Exchange code for tokens
        token_data = await OAuth2Service.exchange_code_for_tokens(
            provider.lower(), code, redirect_uri
        )

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        if not access_token or not refresh_token:
            raise HTTPException(
                status_code=500, detail="Failed to obtain tokens from provider"
            )

        # For Google, we need to get the user's email from the token
        # For now, we'll need to decode the ID token or make an API call
        # Let's use the httpx library to get user info
        import httpx

        user_email = None
        try:
            if provider.lower() == "google":
                # Get user info from Google
                async with httpx.AsyncClient() as client:
                    userinfo_response = await client.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=10.0,
                    )
                    userinfo_response.raise_for_status()
                    userinfo = userinfo_response.json()
                    user_email = userinfo.get("email")
            elif provider.lower() == "microsoft":
                # Get user info from Microsoft
                async with httpx.AsyncClient() as client:
                    userinfo_response = await client.get(
                        "https://graph.microsoft.com/v1.0/me",
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=10.0,
                    )
                    userinfo_response.raise_for_status()
                    userinfo = userinfo_response.json()
                    user_email = userinfo.get("mail") or userinfo.get(
                        "userPrincipalName"
                    )
        except httpx.HTTPError as e:
            logging.error(f"Failed to fetch user info from {provider}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve user information from {provider}. Please try again.",
            )

        if not user_email:
            raise HTTPException(
                status_code=500, detail="Failed to obtain user email from provider"
            )

        # Store tokens in database with user_id
        OAuth2Service.store_oauth2_tokens(
            session=session,
            email=user_email,
            provider=provider.lower(),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user_id=user_id,
        )

        # Redirect to frontend settings page with success message
        frontend_url = os.environ.get("FRONTEND_URL", base_url)
        return RedirectResponse(
            url=f"{frontend_url}/settings?oauth_success=true&email={quote(user_email)}"
        )

    except Exception as e:
        logger.exception("OAuth2 callback error")
        # Redirect to frontend with error
        frontend_url = os.environ.get("FRONTEND_URL", str(request.base_url).rstrip("/"))
        return RedirectResponse(
            url=f"{frontend_url}/settings?oauth_error=true&message={quote(str(e))}"
        )
