import logging
import uuid

from flask import Flask, g, jsonify, request
from app.clients.base import ExternalResponseError, OrchestrationError
from app.routes.make_payment_routes import make_payment_bp
from utils.exceptions import AppError, ValidationError

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.register_blueprint(make_payment_bp)
    _register_correlation_id(app)
    _register_error_handlers(app)
    return app


def _register_correlation_id(app):
    @app.before_request
    def set_correlation_id():
        g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        logger.info("[%s] %s %s", g.correlation_id, request.method, request.path)

    @app.after_request
    def add_correlation_header(response):
        correlation_id = getattr(g, "correlation_id", None)
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        return response


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
