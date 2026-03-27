import logging

import requests

from app.config.settings import make_payment_SERVICE_URL

logger = logging.getLogger(__name__)


def _post_event(event_type: str, payload: dict) -> None:
    """POST a payment lifecycle event to the Make Payment orchestrator.

    Any failure here should bubble up to the webhook handler so the endpoint
    returns 5xx and Stripe retries delivery.
    """
    body = {"eventType": event_type, **payload}
    url = f"{make_payment_SERVICE_URL}/make_payment/payment-events"
    response = requests.post(url, json=body, timeout=5)
    response.raise_for_status()
    logger.info("make_payment_client: posted %s to %s -> %s", event_type, url, response.status_code)


def notify_payment_succeeded(
    payment_id: int,
    invoice_id: int,
    record_id: int,
    payment_intent_id: str,
    attempt_number: int,
    amount: float,
    currency: str,
) -> None:
    _post_event(
        "payment.succeeded",
        {
            "paymentId": payment_id,
            "invoiceId": invoice_id,
            "recordId": record_id,
            "paymentIntentId": payment_intent_id,
            "attemptNumber": attempt_number,
            "amount": amount,
            "currency": currency,
        },
    )


def notify_payment_failed(
    payment_id: int,
    invoice_id: int,
    record_id: int,
    payment_intent_id: str,
    attempt_number: int,
    error_code: str | None,
    error_message: str | None,
) -> None:
    _post_event(
        "payment.failed",
        {
            "paymentId": payment_id,
            "invoiceId": invoice_id,
            "recordId": record_id,
            "paymentIntentId": payment_intent_id,
            "attemptNumber": attempt_number,
            "error": {
                "code": error_code,
                "message": error_message,
            },
        },
    )


def notify_payment_cancelled(
    payment_id: int,
    invoice_id: int,
    record_id: int,
    payment_intent_id: str,
    attempt_number: int,
) -> None:
    _post_event(
        "payment.cancelled",
        {
            "paymentId": payment_id,
            "invoiceId": invoice_id,
            "recordId": record_id,
            "paymentIntentId": payment_intent_id,
            "attemptNumber": attempt_number,
        },
    )
