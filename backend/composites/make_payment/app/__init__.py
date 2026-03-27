from flask import Flask, jsonify
from app.clients.base import ExternalResponseError, OrchestrationError
from app.routes.make_payment_routes import make_payment_bp
from utils.exceptions import AppError, ValidationError


def create_app():
    app = Flask(__name__)
    app.register_blueprint(make_payment_bp)
    _register_error_handlers(app)
    return app


def _register_error_handlers(app):
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
