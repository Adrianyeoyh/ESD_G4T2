from decimal import Decimal, InvalidOperation

from app.config import settings
from app.clients.base import http_request
from utils.exceptions import ValidationError


def create_payment_attempt(
    invoice_id: int,
    record_id: int,
    amount: str | float | Decimal,
    currency: str,
    description: str | None = None,
) -> dict:
    normalized_amount = _as_decimal_string(amount)
    body = {
        "invoiceId": invoice_id,
        "recordId": record_id,
        "amount": normalized_amount,
        "currency": currency,
    }
    if description:
        body["description"] = description
    url = f"{settings.PAYMENT_SERVICE_URL}/payments/intents"
    return http_request("POST", url, json_body=body)


def cancel_payment(payment_id: int) -> dict:
    url = f"{settings.PAYMENT_SERVICE_URL}/payments/{payment_id}/cancel"
    return http_request("POST", url)


def _as_decimal_string(raw_amount: str | float | Decimal) -> str:
    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, TypeError):
        raise ValidationError("amount is invalid")
    if amount <= 0:
        raise ValidationError("amount must be greater than 0")
    return str(amount.quantize(Decimal("0.01")))
