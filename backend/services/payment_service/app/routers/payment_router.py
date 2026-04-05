from fastapi import APIRouter, status

from app.schemas.payment_schema import AtomicPaymentRequest, AtomicPaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])
health_router = APIRouter(tags=["Health"])
payment_service = PaymentService()


@health_router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/process", response_model=AtomicPaymentResponse, status_code=status.HTTP_200_OK)
def process_payment(body: AtomicPaymentRequest) -> AtomicPaymentResponse:
    result = payment_service.process_charge(amount=body.amount, payment_method=body.payment_method)
    return AtomicPaymentResponse.model_validate(result)
