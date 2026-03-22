from sqlalchemy import Column, BigInteger, Numeric, Enum, String, Integer, DateTime
from app.config.db import Base
from common.tools import PaymentStatus
from app.config.settings import DB_SCHEMA
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {"schema": DB_SCHEMA}

    payment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(BigInteger, nullable=False, index=True)
    record_id = Column(BigInteger, nullable=False, index=True)

    provider = Column(String(50), nullable=False, default="stripe")
    payment_intent_id = Column(String(255), nullable=False, unique=True)
    client_secret = Column(String(255), nullable=True)

    attempt_number = Column(Integer, nullable=False, default=1)

    status = Column(
        ENUM(
            PaymentStatus,
            name="payment_status",
            schema="payment_schema",
            create_type=True
        ),
        nullable=False,
        default=PaymentStatus.PENDING
    )

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="sgd")

    error_code = Column(String(100), nullable=True)
    error_message = Column(String, nullable=True)

    paid_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())