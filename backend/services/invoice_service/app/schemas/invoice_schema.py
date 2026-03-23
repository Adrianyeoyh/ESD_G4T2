from pydantic import BaseModel, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class InvoiceCreate(BaseModel):
    record_id: int
    total: Decimal

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class InvoiceUpdateTotal(BaseModel):
    total: Decimal

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class InvoiceResponse(BaseModel):
    invoice_id: int
    record_id: int
    total: Decimal
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,   # replaces orm_mode
    )

    @field_serializer("status")
    def serialize_status(self, v) -> str:
        return v.value if hasattr(v, "value") else v

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        return v.isoformat() if v else None
