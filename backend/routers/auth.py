import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from starlette.responses import JSONResponse

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
    if request.session.get("authenticated"):
        return {"authenticated": True}
    raise HTTPException(status_code=401, detail="Not authenticated")
