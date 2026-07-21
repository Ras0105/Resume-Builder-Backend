# app/schemas.py
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import OrderStatus


# ---------------------------------------------------------------------------
# Resume data — this mirrors the fields your frontend form collects.
# Kept loose (dict-based) at the top level since sections are optional/
# repeatable, but validated enough to catch garbage input early.
# ---------------------------------------------------------------------------

class ResumeContact(BaseModel):
    fullName: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class ResumeData(BaseModel):
    """
    Matches the shape your frontend already builds in script.js.
    Sections are lists of free-form dicts since row shape varies
    (education, experience, projects, etc.) — validated PDF-side
    against the template, not over-constrained here.
    """
    contact: ResumeContact
    summary: Optional[str] = None
    education: list[dict[str, Any]] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[dict[str, Any]] = Field(default_factory=list)
    leadership: list[dict[str, Any]] = Field(default_factory=list)
    coding_profiles: list[dict[str, Any]] = Field(default_factory=list)
    interests: Optional[str] = None
    certifications: Optional[str] = None
    achievements: Optional[str] = None
    custom_sections: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class OrderCreateRequest(BaseModel):
    customer_email: EmailStr
    resume_data: ResumeData
    amount_paise: int = Field(gt=0, description="Amount in smallest currency unit (e.g. paise)")
    currency: str = Field(default="INR", min_length=3, max_length=3)


class OrderCreateResponse(BaseModel):
    """Returned to the frontend so it can redirect to Razorpay checkout."""
    order_id: str                 # your internal Order.id
    razorpay_order_id: str
    razorpay_key_id: str          # public key, safe to expose to client
    amount_paise: int
    currency: str

    model_config = ConfigDict(from_attributes=True)


class OrderStatusResponse(BaseModel):
    order_id: str
    status: OrderStatus
    created_at: datetime
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Webhooks (Razorpay payload shape — only the fields you actually use)
# ---------------------------------------------------------------------------

class RazorpayPaymentEntity(BaseModel):
    id: str
    order_id: str
    status: str
    amount: int
    currency: str
    email: Optional[str] = None


class RazorpayWebhookPayload(BaseModel):
    """
    Raw parsed body of a Razorpay webhook. Note: signature verification
    happens on the RAW request bytes before this model is even built —
    see webhooks.py. This model is for reading the payload afterward.
    """
    event: str
    payload: dict[str, Any]

    def payment_entity(self) -> Optional[RazorpayPaymentEntity]:
        entity = self.payload.get("payment", {}).get("entity")
        return RazorpayPaymentEntity(**entity) if entity else None


# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------

class DownloadLinkResponse(BaseModel):
    download_url: str
    expires_at: datetime


class DownloadTokenPayload(BaseModel):
    """Decoded contents of a signed download token."""
    order_id: str
    pdf_id: str
    expires_at: datetime