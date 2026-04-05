from flask import jsonify, request

from app.services.make_payment_service import MakePaymentService
from utils.exceptions import ValidationError

service = MakePaymentService()


def _success(data: dict, status: int = 200):
    return jsonify({"success": True, "data": data, "error": None}), status


def initiate_payment():
    body = request.get_json(silent=True) or {}
    nric = str(body.get("nric") or "").strip()
    amount = body.get("amount")
    record_id = body.get("recordId")
    payment_method = str(body.get("paymentMethod") or "pm_card_visa").strip()

    if not nric:
        raise ValidationError("nric is required")
    if amount is None:
        raise ValidationError("amount is required")
    if record_id is None:
        raise ValidationError("recordId is required")

    result = service.process_payment(
        nric=nric,
        amount=amount,
        record_id=int(record_id),
        payment_method=payment_method,
    )
    return _success(result, 200)
