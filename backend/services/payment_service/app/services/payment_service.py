import logging
from decimal import Decimal
from uuid import uuid4

import stripe

from app.services import stripe_service

logger = logging.getLogger(__name__)


class PaymentService:
    """Atomic payment processor.

    Responsibilities:
    - Process charge with Stripe using amount + payment method only.
    - Return status + transaction id.
    """

    def process_charge(self, amount: Decimal, payment_method: str) -> dict:
        try:
            intent = stripe_service.create_payment_intent(
                amount=amount,
                currency="sgd",
                description="Atomic payment transaction",
                metadata={},
                payment_method=payment_method,
                confirm=True,
            )
            status = "success" if intent.status == "succeeded" else "failed"
            return {"status": status, "transaction_id": intent.id}
        except stripe.error.StripeError as exc:
            logger.exception("Stripe payment failed")
            return {"status": "failed", "transaction_id": f"tx_failed_{uuid4().hex}"}
