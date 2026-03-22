import logging
from datetime import datetime, timezone
from app.services import stripe_service
from app.services.payment_service import PaymentService
from app.clients import billing_client

logger = logging.getLogger(__name__)

_payment_service = PaymentService()


def handle_webhook_event(payload: bytes, sig_header: str) -> None:
    """Verify and dispatch a Stripe webhook event.

    Raises:
        stripe.error.SignatureVerificationError: for invalid signatures (caller should return 400).
        ValueError: if the payload is malformed.
    """
    event = stripe_service.construct_webhook_event(payload, sig_header)

    event_type = event["type"]
    intent = event["data"]["object"]
    payment_intent_id = intent["id"]

    logger.info("webhook_service: received event %s for pi=%s", event_type, payment_intent_id)

    if event_type == "payment_intent.succeeded":
        paid_at = datetime.fromtimestamp(intent.get("created", 0), tz=timezone.utc)
        payment = _payment_service.mark_succeeded(
            payment_intent_id=payment_intent_id,
            paid_at=paid_at,
        )
        billing_client.notify_payment_succeeded(
            payment_id=payment.payment_id,
            invoice_id=payment.invoice_id,
            record_id=payment.record_id,
            payment_intent_id=payment.payment_intent_id,
            attempt_number=payment.attempt_number,
            amount=float(payment.amount),
            currency=payment.currency,
        )

    elif event_type == "payment_intent.payment_failed":
        last_error = intent.get("last_payment_error") or {}
        error_code = last_error.get("code")
        error_message = last_error.get("message")
        payment = _payment_service.mark_failed(
            payment_intent_id=payment_intent_id,
            error_code=error_code,
            error_message=error_message,
        )
        billing_client.notify_payment_failed(
            payment_id=payment.payment_id,
            invoice_id=payment.invoice_id,
            record_id=payment.record_id,
            payment_intent_id=payment.payment_intent_id,
            attempt_number=payment.attempt_number,
            error_code=error_code,
            error_message=error_message,
        )

    elif event_type == "payment_intent.canceled":
        # Look up the payment by payment_intent_id to get the payment_id for mark_cancelled
        from app.config.db import SessionLocal
        from app.repositories.payment_repository import PaymentRepository
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            payment_row = repo.get_by_payment_intent_id(payment_intent_id)
        finally:
            db.close()

        if payment_row:
            payment = _payment_service.mark_cancelled(payment_id=payment_row.payment_id)
            billing_client.notify_payment_cancelled(
                payment_id=payment.payment_id,
                invoice_id=payment.invoice_id,
                record_id=payment.record_id,
                payment_intent_id=payment.payment_intent_id,
                attempt_number=payment.attempt_number,
            )
        else:
            logger.warning(
                "webhook_service: received payment_intent.canceled for unknown pi=%s",
                payment_intent_id,
            )

    else:
        logger.info("webhook_service: ignoring unhandled event type %s", event_type)
