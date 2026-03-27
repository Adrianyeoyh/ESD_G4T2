from pydantic import BaseModel, ConfigDict, Field, field_serializer
from pydantic.alias_generators import to_camel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class PaymentIntentCreate(BaseModel):
    invoice_id: int
    record_id: int
    amount: Decimal = Field(gt=0)
    currency: str
    description: Optional[str] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PaymentReadResponse(BaseModel):
    payment_id: int
    invoice_id: int
    record_id: int
    provider: str
    payment_intent_id: str
    attempt_number: int
    status: str
    amount: Decimal
    currency: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    paid_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @field_serializer("status")
    def serialize_status(self, v) -> str:
        return v.value if hasattr(v, "value") else v

    @field_serializer("paid_at", "cancelled_at", "created_at", "updated_at")
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        return v.isoformat() if v else None


class PaymentResponse(PaymentReadResponse):
    client_secret: Optional[str] = None
