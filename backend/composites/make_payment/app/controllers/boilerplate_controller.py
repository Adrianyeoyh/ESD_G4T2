from flask import jsonify, request

from app.services.boilerplate_service import ExternalResponseError, MakePaymentService, OrchestrationError
from utils.exceptions import AppError, ValidationError

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


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(exc):
        return jsonify({"success": False, "data": None, "error": exc.message, "errorCode": "VALIDATION_ERROR"}), 400

    @app.errorhandler(OrchestrationError)
    def handle_orchestration_error(exc):
        payload = {
            "success": False,
            "data": None,
            "error": exc.message,
            "errorCode": exc.error_code,
        }
        payload.update(exc.extra)
        return jsonify(payload), exc.status_code

    @app.errorhandler(ExternalResponseError)
    def handle_external_error(exc):
        return jsonify(
            {
                "success": False,
                "data": None,
                "error": "Unexpected dependency response",
                "errorCode": "DEPENDENCY_ERROR",
                "dependencyStatus": exc.status_code,
                "dependencyPayload": exc.payload,
            }
        ), 502

    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return jsonify({"success": False, "data": None, "error": exc.message, "errorCode": "APP_ERROR"}), exc.status_code

    @app.errorhandler(Exception)
    def handle_generic_error(_exc):
        return jsonify(
            {"success": False, "data": None, "error": "Internal server error", "errorCode": "INTERNAL_SERVER_ERROR"}
        ), 500
