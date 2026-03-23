from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
import stripe

from app.config.db import get_db
from app.schemas.payment_schema import PaymentIntentCreate, PaymentResponse
from app.services.payment_service import PaymentService
from app.services import webhook_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/intents", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(body: PaymentIntentCreate, db: Session = Depends(get_db)):
    svc = PaymentService(db)
    payment = svc.create_payment_attempt(
        invoice_id=body.invoiceId,
        record_id=body.recordId,
        amount=body.amount,
        currency=body.currency,
        description=body.description,
    )
    return PaymentResponse.from_orm_model(payment)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    svc = PaymentService(db)
    return PaymentResponse.from_orm_model(svc.get_payment(payment_id))


@router.get("/invoice/{invoice_id}", response_model=list[PaymentResponse])
def list_payments_by_invoice(invoice_id: int, db: Session = Depends(get_db)):
    svc = PaymentService(db)
    return [PaymentResponse.from_orm_model(p) for p in svc.list_payments_by_invoice_id(invoice_id)]


@router.get("/invoice/{invoice_id}/latest", response_model=PaymentResponse)
def get_latest_payment_by_invoice(invoice_id: int, db: Session = Depends(get_db)):
    svc = PaymentService(db)
    return PaymentResponse.from_orm_model(svc.get_latest_payment_by_invoice_id(invoice_id))


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
def cancel_payment(payment_id: int, db: Session = Depends(get_db)):
    svc = PaymentService(db)
    return PaymentResponse.from_orm_model(svc.mark_cancelled(payment_id))


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def handle_webhook(request: Request):
    """Stripe webhook receiver. Reads raw bytes — must not go through Pydantic body parsing."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_service.handle_webhook_event(payload, sig_header)
    return {"received": True}
