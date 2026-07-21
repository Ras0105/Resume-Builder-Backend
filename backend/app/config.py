# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- App ----
    ENV: str = "development"                 # development | production
    FRONTEND_URL: str = "http://localhost:5500"  # used for CORS + email links

    # ---- Database ----
    DATABASE_URL: str                        # e.g. postgresql+psycopg://user:pass@host:5432/dbname

    # ---- Razorpay ----
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    RAZORPAY_WEBHOOK_SECRET: str             # separate secret used only to verify webhook signatures

    # ---- Storage (Supabase / S3-compatible) ----
    STORAGE_BUCKET: str
    STORAGE_ENDPOINT_URL: str                # e.g. Supabase project storage URL or R2 endpoint
    STORAGE_ACCESS_KEY: str
    STORAGE_SECRET_KEY: str

    # ---- Signed download links ----
    DOWNLOAD_LINK_SECRET: str                # used to sign/verify one-time download tokens
    DOWNLOAD_LINK_EXPIRY_MINUTES: int = 15

    # ---- Email (Resend / SendGrid) ----
    EMAIL_API_KEY: str
    EMAIL_FROM_ADDRESS: str = "no-reply@yourdomain.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — import this, not Settings() directly."""
    return Settings()


# Usage elsewhere (e.g. in services/payment.py):
# from app.config import get_settings
# settings = get_settings()
# client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))