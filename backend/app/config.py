# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- App ----
    ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:5500"

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