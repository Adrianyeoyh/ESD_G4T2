import logging
from datetime import datetime, timezone
from app.services import stripe_service
from app.clients import make_payment_client
from app.config.db import SessionLocal

logger = logging.getLogger(__name__)


def handle_webhook_event(payload: bytes, sig_header: str) -> None:
    """Verify and dispatch a Stripe webhook event.

    Webhooks are background events — not part of a FastAPI request/response cycle.
    We cannot use Depends(get_db) here, so each handler opens its own session.

    Raises:
        stripe.error.SignatureVerificationError: for invalid signatures (caller returns 400).
        ValueError: if the payload is malformed.
    """
    event = stripe_service.construct_webhook_event(payload, sig_header)

    event_type = event["type"]
    intent = event["data"]["object"]
    payment_intent_id = intent["id"]

    logger.info("webhook_service: received event %s for pi=%s", event_type, payment_intent_id)

    if event_type == "payment_intent.succeeded":
        _handle_succeeded(payment_intent_id, intent)

    elif event_type == "payment_intent.payment_failed":
        _handle_failed(payment_intent_id, intent)

    elif event_type == "payment_intent.canceled":
        _handle_cancelled(payment_intent_id)

    else:
        logger.info("webhook_service: ignoring unhandled event type %s", event_type)


def _handle_succeeded(payment_intent_id: str, intent: dict) -> None:
    from app.services.payment_service import PaymentService
    db = SessionLocal()
    try:
        svc = PaymentService(db)
        paid_at = datetime.fromtimestamp(intent.get("created", 0), tz=timezone.utc)
        payment = svc.mark_succeeded(payment_intent_id=payment_intent_id, paid_at=paid_at)
        make_payment_client.notify_payment_succeeded(
            payment_id=payment.payment_id,
            invoice_id=payment.invoice_id,
            record_id=payment.record_id,
            payment_intent_id=payment.payment_intent_id,
            attempt_number=payment.attempt_number,
            amount=float(payment.amount),
            currency=payment.currency,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _handle_failed(payment_intent_id: str, intent: dict) -> None:
    from app.services.payment_service import PaymentService
    db = SessionLocal()
    try:
        svc = PaymentService(db)
        last_error = intent.get("last_payment_error") or {}
        error_code = last_error.get("code")
        error_message = last_error.get("message")
        payment = svc.mark_failed(
            payment_intent_id=payment_intent_id,
            error_code=error_code,
            error_message=error_message,
        )
        make_payment_client.notify_payment_failed(
            payment_id=payment.payment_id,
            invoice_id=payment.invoice_id,
            record_id=payment.record_id,
            payment_intent_id=payment.payment_intent_id,
            attempt_number=payment.attempt_number,
            error_code=error_code,
            error_message=error_message,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _handle_cancelled(payment_intent_id: str) -> None:
    from app.services.payment_service import PaymentService
    db = SessionLocal()
    try:
        svc = PaymentService(db)
        payment = svc.mark_cancelled_by_webhook(payment_intent_id=payment_intent_id)
        make_payment_client.notify_payment_cancelled(
            payment_id=payment.payment_id,
            invoice_id=payment.invoice_id,
            record_id=payment.record_id,
            payment_intent_id=payment.payment_intent_id,
            attempt_number=payment.attempt_number,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
