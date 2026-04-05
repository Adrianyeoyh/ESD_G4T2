from decimal import Decimal, InvalidOperation

from app.clients.base import http_request
from app.config import settings
from utils.exceptions import ValidationError


def process_payment(amount: str | float | Decimal, payment_method: str) -> dict:
    normalized_amount = _as_decimal_string(amount)
    method = str(payment_method or "").strip()
    if not method:
        raise ValidationError("paymentMethod is required")

    body = {
        "amount": normalized_amount,
        "paymentMethod": method,
    }
    url = f"{settings.PAYMENT_SERVICE_URL}/payments/process"
    return http_request("POST", url, json_body=body)


def _as_decimal_string(raw_amount: str | float | Decimal) -> str:
    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, TypeError):
        raise ValidationError("amount is invalid")
    if amount <= 0:
        raise ValidationError("amount must be greater than 0")
    return str(amount.quantize(Decimal("0.01")))
