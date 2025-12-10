from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.database import create_db_and_tables
from backend.models import ProcessedEmail
from backend.services.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    print("Startup: Database tables created.")
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    print("Shutdown: App stopping.")

from backend.routers import dashboard, settings, history

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(
    title="Receipt Forwarder API",
    lifespan=lifespan
)

app.include_router(dashboard.router)
app.include_router(settings.router)
app.include_router(history.router)

# Mount API first
@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

# Serve Frontend (Dist)
# Check if frontend/dist exists (Production)
frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")
    
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
    return {"status": "ok", "message": "Receipt Forwarder Backend Running (Frontend not built)"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
