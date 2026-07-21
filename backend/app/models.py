# app/models.py
import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum,
    ForeignKey,
    Text,
    Boolean,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class OrderStatus(str, enum.Enum):
    PENDING = "pending"       # order created, awaiting payment
    PAID = "paid"              # webhook verified payment
    GENERATING = "generating"  # PDF being built
    COMPLETED = "completed"    # PDF ready, email sent
    FAILED = "failed"          # payment failed or PDF generation errored
    EXPIRED = "expired"        # pending order too old, abandoned checkout


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)

    # Contact info so we can email the PDF even if the browser tab is closed
    customer_email = Column(String, nullable=False, index=True)

    # Snapshot of the resume form data at checkout time — the single source
    # of truth the PDF is generated from. Never trust anything sent later.
    resume_data = Column(JSONB, nullable=False)

    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)
    amount_paise = Column(Integer, nullable=False)  # store amount in smallest currency unit
    currency = Column(String, nullable=False, default="INR")

    # Razorpay identifiers
    razorpay_order_id = Column(String, unique=True, index=True, nullable=True)
    razorpay_payment_id = Column(String, unique=True, index=True, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    generated_pdf = relationship(
        "GeneratedPdf", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    webhook_events = relationship(
        "WebhookEvent", back_populates="order", cascade="all, delete-orphan"
    )


class GeneratedPdf(Base):
    __tablename__ = "generated_pdfs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    order_id = Column(UUID(as_uuid=False), ForeignKey("orders.id"), nullable=False, unique=True)

    storage_key = Column(String, nullable=False)     # path/key in the storage bucket
    download_token = Column(String, unique=True, index=True, nullable=False)  # signed token component
    token_expires_at = Column(DateTime(timezone=True), nullable=False)

    email_sent = Column(Boolean, default=False, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    order = relationship("Order", back_populates="generated_pdf")


class WebhookEvent(Base):
    """
    Audit log of every webhook received — even ones that fail verification.
    Critical for debugging payment disputes and for idempotency (Razorpay
    can retry the same webhook; check this table before reprocessing).
    """
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    order_id = Column(UUID(as_uuid=False), ForeignKey("orders.id"), nullable=True)

    razorpay_event_id = Column(String, unique=True, index=True, nullable=True)
    event_type = Column(String, nullable=False)          # e.g. "payment.captured"
    signature_valid = Column(Boolean, nullable=False)
    raw_payload = Column(Text, nullable=False)            # store raw body for audit/debug

    received_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    order = relationship("Order", back_populates="webhook_events")