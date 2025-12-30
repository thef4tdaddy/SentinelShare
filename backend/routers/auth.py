import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session
from starlette.responses import JSONResponse, RedirectResponse

from backend.database import get_session
from backend.services.oauth2_service import OAuth2Service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
def login(request: Request, login_data: LoginRequest):
    expected_password = os.environ.get("DASHBOARD_PASSWORD")
    if not expected_password:
        return JSONResponse({"error": "Auth not configured"}, status_code=500)

    if login_data.password == expected_password:
        request.session["authenticated"] = True
        return {"status": "success"}

    raise HTTPException(status_code=401, detail="Invalid password")


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "logged_out"}


@router.get("/me")
def check_auth(request: Request):
    # Allow access if authenticated OR if running in No-Auth Dev Mode
    if request.session.get("authenticated") or not os.environ.get("DASHBOARD_PASSWORD"):
        return {"authenticated": True}
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
    request: Request, provider: str, code: str, state: str, error: str | None = None, session: Session = Depends(get_session)
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
                    user_email = userinfo.get("mail") or userinfo.get("userPrincipalName")
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

        # Store tokens in database
        OAuth2Service.store_oauth2_tokens(
            session=session,
            email=user_email,
            provider=provider.lower(),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

        # Redirect to frontend settings page with success message
        frontend_url = os.environ.get("FRONTEND_URL", base_url)
        return RedirectResponse(
            url=f"{frontend_url}/settings?oauth_success=true&email={user_email}"
        )

    except Exception as e:
        import logging

        logging.exception("OAuth2 callback error")
        # Redirect to frontend with error
        frontend_url = os.environ.get("FRONTEND_URL", str(request.base_url).rstrip("/"))
        return RedirectResponse(
            url=f"{frontend_url}/settings?oauth_error=true&message={str(e)}"
        )
