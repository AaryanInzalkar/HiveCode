"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from hivecode.api.routers import auth, events, tasks
from hivecode.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    print(f"Starting HiveCode API in {settings.environment} mode")
    yield
    # Shutdown
    print("Shutting down HiveCode API")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="HiveCode API",
        description="A verification-first, self-correcting AI software engineering pipeline",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — same-origin in production, allow localhost in dev
    if settings.environment == "local":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
    app.include_router(events.router, prefix="/api/v1/events", tags=["events"])

    @app.get("/health")
    async def health_check() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": "0.1.0"})

    @app.get("/api/v1/health")
    async def api_health_check() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": "0.1.0"})

    return app


app = create_app()
