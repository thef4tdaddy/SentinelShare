import os
from contextlib import asynccontextmanager

from backend.routers import actions, auth, dashboard, history, settings
from backend.services.scheduler import start_scheduler, stop_scheduler
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

# actually CI says backend.models.ProcessedEmail imported but unused.
# backend.database.create_db_and_tables imported but unused.


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Check/Run Alembic Migrations (Handles legacy DB stamping + new upgrades)
    try:
        from backend.migration_utils import run_migrations

        run_migrations()
    except Exception as e:
        print(f"Startup Migration Error: {e}")

    print("Startup: Database checks complete.")
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    print("Shutdown: App stopping.")


app = FastAPI(title="Receipt Forwarder API", lifespan=lifespan)


# Custom Auth Middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Allow public endpoints
    if (
        path.startswith("/api/auth")
        or path in ["/api/health", "/health"]
        or path.startswith("/assets")
        or path == "/"
        or not path.startswith("/api")  # Serve frontend assets/SPA routes freely
    ):
        return await call_next(request)

    # Check Authentication for protected API routes
    if not request.session.get("authenticated"):
        # If DASHBOARD_PASSWORD is not set, allow access (Backward compatibility/Dev mode)
        if not os.environ.get("DASHBOARD_PASSWORD"):
            return await call_next(request)

        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    return await call_next(request)


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(settings.router)
app.include_router(history.router)
app.include_router(actions.router)

# Session Middleware (Required for Auth) - Added LAST to be OUTERMOST (runs first)
app.add_middleware(
    SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "CHANGEME_DEV_KEY")
)


# Mount API first
@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


# Serve Frontend (Dist)
# Check if frontend/dist exists (Production)
frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_dist_path):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(frontend_dist_path, "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API calls to pass through (handled above if matched, but here we need to be careful)
        if full_path.startswith("api/"):
            return {"error": "API endpoint not found"}

        # Serve index.html for everything else (SPA)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))


@app.get("/")
def read_root():
    # If dist exists, serve index.html
    if os.path.exists(frontend_dist_path):
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))
    return {
        "status": "ok",
        "message": "Receipt Forwarder Backend Running (Frontend not built)",
    }


# Removed redefined health_check
