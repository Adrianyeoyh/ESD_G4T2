import logging
import requests
from app.config.settings import BILLING_SERVICE_URL

logger = logging.getLogger(__name__)


def _post_event(event_type: str, payload: dict) -> None:
    """Internal helper — POST an event to the Billing composite.

    Catches and logs all errors silently since Billing may not be running yet.
    """
    body = {"eventType": event_type, **payload}
    try:
        url = f"{BILLING_SERVICE_URL}/billing/payment-events"
        resp = requests.post(url, json=body, timeout=5)
        resp.raise_for_status()
        logger.info("billing_client: posted %s to %s — %s", event_type, url, resp.status_code)
    except Exception as e:
        logger.warning("billing_client: failed to post %s — %s", event_type, str(e))


def notify_payment_succeeded(
    payment_id: int,
    invoice_id: int,
    record_id: int,
    payment_intent_id: str,
    attempt_number: int,
    amount: float,
    currency: str,
) -> None:
    _post_event("payment.succeeded", {
        "paymentId": payment_id,
        "invoiceId": invoice_id,
        "recordId": record_id,
        "paymentIntentId": payment_intent_id,
        "attemptNumber": attempt_number,
        "amount": amount,
        "currency": currency,
    })


def notify_payment_failed(
    payment_id: int,
    invoice_id: int,
    record_id: int,
    payment_intent_id: str,
    attempt_number: int,
    error_code: str | None,
    error_message: str | None,
) -> None:
    _post_event("payment.failed", {
        "paymentId": payment_id,
        "invoiceId": invoice_id,
        "recordId": record_id,
        "paymentIntentId": payment_intent_id,
        "attemptNumber": attempt_number,
        "error": {
            "code": error_code,
            "message": error_message,
        },
    })


def notify_payment_cancelled(
    payment_id: int,
    invoice_id: int,
    record_id: int,
    payment_intent_id: str,
    attempt_number: int,
) -> None:
    _post_event("payment.cancelled", {
        "paymentId": payment_id,
        "invoiceId": invoice_id,
        "recordId": record_id,
        "paymentIntentId": payment_intent_id,
        "attemptNumber": attempt_number,
    })
