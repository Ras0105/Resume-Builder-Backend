# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- App ----
    ENV: str = "development"
    # Comma-separated list of allowed CORS origins, e.g.
    # "https://resume-builder-backend-ecru.vercel.app,http://localhost:5500"
    FRONTEND_URL: str = "http://localhost:5500"
    # Base URL of THIS backend (Railway), used to build links to backend
    # routes like /api/download/{token}. Deliberately separate from
    # FRONTEND_URL — that one is for CORS and may hold multiple origins,
    # which would corrupt a link if reused here.
    BACKEND_URL: str = "http://localhost:8000"

    @property
    def allowed_origins(self) -> list[str]:
        # Origins must never have a trailing slash — browsers never send one
        # in the Origin header, so a mismatch here silently breaks every
        # CORS preflight (manifests as 400 on OPTIONS, request never reaches
        # the route).
        return [origin.strip().rstrip("/") for origin in self.FRONTEND_URL.split(",") if origin.strip()]

    # ---- Database ----
    DATABASE_URL: str

    # ---- Razorpay ----
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    RAZORPAY_WEBHOOK_SECRET: str

    # ---- Storage (Supabase / S3-compatible) ----
    STORAGE_BUCKET: str
    STORAGE_ENDPOINT_URL: str
    STORAGE_ACCESS_KEY: str
    STORAGE_SECRET_KEY: str

    # ---- Signed download links ----
    DOWNLOAD_LINK_SECRET: str
    DOWNLOAD_LINK_EXPIRY_MINUTES: int = 15

    # ---- Email (Gmail SMTP) ----
    EMAIL_FROM_ADDRESS: str      # your Gmail address — read from .env, never hardcoded
    EMAIL_APP_PASSWORD: str      # Gmail app password — read from .env, never hardcoded

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()