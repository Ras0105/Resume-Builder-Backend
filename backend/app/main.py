# app/main.py
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine
from app.routers import orders, webhooks, downloads

settings = get_settings()

logging.basicConfig(
    level=logging.INFO if settings.ENV == "production" else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("resume_builder")

app = FastAPI(
    title="Resume Builder API",
    version="1.0.0",
    # Hide interactive docs in production — no reason to expose your API
    # surface/schemas publicly once this is live.
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
    openapi_url="/openapi.json" if settings.ENV != "production" else None,
)

# ---------------------------------------------------------------------------
# CORS — only your actual frontend origin should be allowed to call this API
# with credentials. Do NOT use "*" here once real payment data is involved.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# Startup: create tables if they don't exist yet.
# Fine for early development — switch to Alembic migrations before this
# schema needs to change safely in production with real customer data.
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured. Environment: %s", settings.ENV)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(orders.router)
app.include_router(webhooks.router)
app.include_router(downloads.router)


# ---------------------------------------------------------------------------
# Health check — useful for Railway/Render/Fly's uptime monitoring
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Generic error handler — avoids leaking stack traces/internals to clients
# on unexpected exceptions, while still logging the full detail server-side.
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong. Please try again."},
    )