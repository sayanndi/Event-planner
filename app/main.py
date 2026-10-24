"""FastAPI application: JSON API under /api and the web UI at /."""
from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, load_settings
from app.ideas import IdeaGenerator, build_idea_generator
from app.models import EventPlan, PlanRequest
from app.planner import build_plan
from app.security import SECURITY_HEADERS, RateLimiter

STATIC_DIR = Path(__file__).parent / "static"
logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, idea_generator: IdeaGenerator | None = None) -> FastAPI:
    """Application factory; arguments let tests inject fakes."""
    settings = settings or load_settings()
    generator = idea_generator or build_idea_generator(settings)
    limiter = RateLimiter(settings.rate_limit_per_minute)

    # Interactive docs are off: they load third-party scripts that the CSP blocks.
    app = FastAPI(title="Event Planner", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def protect(request: Request, call_next):
        length = request.headers.get("content-length", "")
        if length.isdigit() and int(length) > settings.max_body_bytes:
            response = JSONResponse({"detail": "Request body too large."}, status_code=413)
        else:
            response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    def enforce_rate_limit(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        if not limiter.allow(client):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait a minute and try again.",
                headers={"Retry-After": "60"},
            )

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "ai_enabled": settings.ai_enabled}

    # A plain ``def`` endpoint runs in FastAPI's thread pool, so the blocking
    # LLM call never freezes the event loop.
    @app.post("/api/plan", response_model=EventPlan, dependencies=[Depends(enforce_rate_limit)])
    def create_plan(payload: PlanRequest) -> EventPlan:
        return build_plan(payload, generator)

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


load_dotenv()  # read .env for local development; real environment variables win
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = create_app()
