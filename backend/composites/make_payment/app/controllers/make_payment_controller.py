from flask import jsonify, request

from app.services.make_payment_service import MakePaymentService
from utils.exceptions import ValidationError

service = MakePaymentService()


def _success(data: dict, status: int = 200):
    return jsonify({"success": True, "data": data, "error": None}), status


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
    body = request.get_json(silent=True) or {}
    result = service.handle_payment_event(body)
    return _success(result, 200)
