# app/services/storage.py
import secrets
from datetime import datetime, timedelta, timezone

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

settings = get_settings()


class StorageError(Exception):
    """Raised when uploading or presigning fails."""
    pass


_s3_client = boto3.client(
    "s3",
    endpoint_url=settings.STORAGE_ENDPOINT_URL,
    aws_access_key_id=settings.STORAGE_ACCESS_KEY,
    aws_secret_access_key=settings.STORAGE_SECRET_KEY,
    config=BotoConfig(signature_version="s3v4"),
    region_name="auto",  # required by some S3-compatible providers (e.g. R2), ignored by others
)


def _build_storage_key(order_id: str) -> str:
    """
    Keys are namespaced by order id and not guessable from anything
    public-facing. The actual object is never listed or served directly —
    always through a presigned URL with a short TTL.
    """
    return f"resumes/{order_id}/resume.pdf"


def upload_pdf(order_id: str, pdf_bytes: bytes) -> str:
    """
    Uploads the generated PDF to the private bucket. Returns the storage
    key to persist on GeneratedPdf.storage_key — never a public URL.
    The bucket itself should have public access fully disabled; the only
    way to reach an object is via get_presigned_download_url() below.
    """
    key = _build_storage_key(order_id)
    try:
        _s3_client.put_object(
            Bucket=settings.STORAGE_BUCKET,
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ContentDisposition="attachment; filename=\"resume.pdf\"",
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError(f"Failed to upload PDF for order {order_id}: {exc}") from exc

    return key


def get_presigned_download_url(storage_key: str, expires_in_seconds: int = 120) -> str:
    """
    Generates a short-lived presigned URL for a single download. This is
    a second, independent layer of expiry on top of GeneratedPdf's own
    token_expires_at — even if someone got hold of a valid download token,
    the underlying object URL itself goes stale within minutes.
    """
    try:
        return _s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.STORAGE_BUCKET, "Key": storage_key},
            ExpiresIn=expires_in_seconds,
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError(f"Failed to generate download URL for {storage_key}: {exc}") from exc


def delete_pdf(storage_key: str) -> None:
    """
    Optional cleanup — call from a scheduled job to remove PDFs past
    their retention window (e.g. 24h after generation), so paid resumes
    don't sit in the bucket indefinitely.
    """
    try:
        _s3_client.delete_object(Bucket=settings.STORAGE_BUCKET, Key=storage_key)
    except (BotoCoreError, ClientError) as exc:
        raise StorageError(f"Failed to delete {storage_key}: {exc}") from exc


def generate_download_token() -> str:
    """
    Generates the opaque, unguessable token stored on GeneratedPdf.download_token
    and embedded in the email link (/api/download/{token}). 32 bytes of
    URL-safe randomness — not derived from order_id or any predictable value.
    """
    return secrets.token_urlsafe(32)


def build_download_link(frontend_or_api_base_url: str, token: str) -> str:
    """Assembles the full link that goes in the email/UI."""
    return f"{frontend_or_api_base_url.rstrip('/')}/api/download/{token}"


def token_expiry_datetime() -> datetime:
    """Computes the expiry timestamp to store alongside a newly generated token."""
    return datetime.now(timezone.utc) + timedelta(minutes=settings.DOWNLOAD_LINK_EXPIRY_MINUTES)