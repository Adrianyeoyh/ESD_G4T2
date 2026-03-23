from pydantic import BaseModel
from typing import Optional


class InvoiceCreate(BaseModel):
    recordId: int
    total: float


class InvoiceUpdateTotal(BaseModel):
    total: float


class InvoiceResponse(BaseModel):
    invoiceId: int
    recordId: int
    total: float
    status: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj):
        return cls(
            invoiceId=obj.invoice_id,
            recordId=obj.record_id,
            total=float(obj.total),
            status=obj.status.value,
            createdAt=obj.created_at.isoformat() if obj.created_at else None,
            updatedAt=obj.updated_at.isoformat() if obj.updated_at else None,
        )
