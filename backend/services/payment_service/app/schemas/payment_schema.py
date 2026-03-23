from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class PaymentIntentCreate(BaseModel):
    invoiceId: int
    recordId: int
    amount: Decimal
    currency: str
    description: Optional[str] = None


class PaymentResponse(BaseModel):
    paymentId: int
    invoiceId: int
    recordId: int
    provider: str
    paymentIntentId: str
    clientSecret: Optional[str] = None
    attemptNumber: int
    status: str
    amount: float
    currency: str
    errorCode: Optional[str] = None
    errorMessage: Optional[str] = None
    paidAt: Optional[str] = None
    cancelledAt: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj):
        return cls(
            paymentId=obj.payment_id,
            invoiceId=obj.invoice_id,
            recordId=obj.record_id,
            provider=obj.provider,
            paymentIntentId=obj.payment_intent_id,
            clientSecret=obj.client_secret,
            attemptNumber=obj.attempt_number,
            status=obj.status.value,
            amount=float(obj.amount),
            currency=obj.currency,
            errorCode=obj.error_code,
            errorMessage=obj.error_message,
            paidAt=obj.paid_at.isoformat() if obj.paid_at else None,
            cancelledAt=obj.cancelled_at.isoformat() if obj.cancelled_at else None,
            createdAt=obj.created_at.isoformat() if obj.created_at else None,
            updatedAt=obj.updated_at.isoformat() if obj.updated_at else None,
        )
