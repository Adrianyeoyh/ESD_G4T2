from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.orm import Session
import stripe

from app.config.db import get_db
from app.schemas.payment_schema import PaymentIntentCreate, PaymentResponse, PaymentReadResponse
from app.services.payment_service import PaymentService
from app.services.webhook_handler import process_webhook_event

router = APIRouter(prefix="/payments", tags=["Payments"])
health_router = APIRouter(tags=["Health"])


# ── Service dependency ──────────────────────────────────────────────────────
@health_router.get("/health")
def health():
    return {"status": "ok"}


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


# ── Routes ──────────────────────────────────────────────────────────────────

@router.post("/intents", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    body: PaymentIntentCreate,
    svc: PaymentService = Depends(get_payment_service),
):
    try:
        payment = svc.create_payment_attempt(
            invoice_id=body.invoice_id,
            record_id=body.record_id,
            amount=body.amount,
            currency=body.currency,
            description=body.description,
        )
        return PaymentResponse.model_validate(payment)
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Stripe unavailable: {exc.user_message or str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Payment intent failed: {exc}")


@router.get("/{payment_id}", response_model=PaymentReadResponse)
def get_payment(payment_id: int, svc: PaymentService = Depends(get_payment_service)):
    return PaymentReadResponse.model_validate(svc.get_payment(payment_id))


@router.get("/invoice/{invoice_id}", response_model=list[PaymentReadResponse])
def list_payments_by_invoice(invoice_id: int, svc: PaymentService = Depends(get_payment_service)):
    return [PaymentReadResponse.model_validate(p) for p in svc.list_payments_by_invoice_id(invoice_id)]


@router.get("/invoice/{invoice_id}/latest", response_model=PaymentReadResponse)
def get_latest_payment_by_invoice(invoice_id: int, svc: PaymentService = Depends(get_payment_service)):
    return PaymentReadResponse.model_validate(svc.get_latest_payment_by_invoice_id(invoice_id))


@router.post("/{payment_id}/cancel", response_model=PaymentReadResponse)
def cancel_payment(payment_id: int, svc: PaymentService = Depends(get_payment_service)):
    return PaymentReadResponse.model_validate(svc.mark_cancelled(payment_id))


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def handle_webhook(request: Request):
    """Stripe webhook receiver. Reads raw bytes — must not go through Pydantic body parsing."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        process_webhook_event(payload, sig_header)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {exc}")

    return {"received": True}
