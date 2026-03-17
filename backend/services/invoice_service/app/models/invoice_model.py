from sqlalchemy import Column, BigInteger, Numeric, Enum, String, Integer, DateTime, func
from app.config.db import Base
from shared.types.tools import InvoiceStatus
from config.settings import DB_SCHEMA


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = {"schema": DB_SCHEMA}

    invoice_id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, nullable=False, unique=True)
    total = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.UNPAID)
    payment_intent_id = Column(String(255), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_payment_error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())