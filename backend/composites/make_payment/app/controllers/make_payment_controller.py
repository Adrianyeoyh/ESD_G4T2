import hmac

from flask import jsonify, request

from app.config.settings import INTERNAL_API_KEY
from app.services.make_payment_service import MakePaymentService
from utils.exceptions import ValidationError

service = MakePaymentService()


def _success(data: dict, status: int = 200):
    return jsonify({"success": True, "data": data, "error": None}), status


def _require_internal_api_key():
    """Return a 401 response if the X-Internal-Api-Key header is missing or wrong."""
    provided = request.headers.get("X-Internal-Api-Key", "")
    if not hmac.compare_digest(provided, INTERNAL_API_KEY):
        return jsonify({"success": False, "data": None, "error": "Unauthorized", "errorCode": "UNAUTHORIZED"}), 401
    return None


def initiate_payment():
    body = request.get_json(silent=True) or {}
    invoice_id = body.get("invoiceId")
    if not invoice_id:
        raise ValidationError("invoiceId is required")

    currency = body.get("currency")
    description = body.get("description")
    result = service.initiate_payment(invoice_id=invoice_id, currency=currency, description=description)
    return _success(result, 201)


def retry_payment():
    body = request.get_json(silent=True) or {}
    invoice_id = body.get("invoiceId")
    if not invoice_id:
        raise ValidationError("invoiceId is required")

    currency = body.get("currency")
    description = body.get("description")
    result = service.retry_payment(invoice_id=invoice_id, currency=currency, description=description)
    return _success(result, 201)


def handle_payment_event():
    auth_error = _require_internal_api_key()
    if auth_error:
        return auth_error

    body = request.get_json(silent=True) or {}
    result = service.handle_payment_event(body)
    return _success(result, 200)
