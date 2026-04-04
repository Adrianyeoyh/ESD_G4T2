"""
Global error handlers and utilities for consistent error responses
"""
from flask import jsonify
from requests.exceptions import RequestException, Timeout, ConnectionError

from utils.exceptions import (
    AppError,
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)


class ErrorResponse:
    """Standardized error response format"""
    def __init__(self, message: str, error_code: str, status_code: int, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self):
        response = {
            "message": self.message,
            "error": self.error_code,
        }
        if self.details:
            response["details"] = self.details
        return response


def handle_request_exception(error: RequestException) -> tuple:
    """Handle requests library exceptions"""
    if isinstance(error, Timeout):
        err = ErrorResponse(
            message="Downstream service request timed out. Please try again.",
            error_code="DOWNSTREAM_TIMEOUT",
            status_code=503,
            details={"timeout_seconds": 8}
        )
    elif isinstance(error, ConnectionError):
        err = ErrorResponse(
            message="Unable to reach downstream service. Service may be unavailable.",
            error_code="DOWNSTREAM_CONNECTION_ERROR",
            status_code=503,
        )
    else:
        err = ErrorResponse(
            message="Downstream service error. Please try again.",
            error_code="DOWNSTREAM_ERROR",
            status_code=503,
            details={"original_error": str(error)[:100]}
        )
    return jsonify(err.to_dict()), err.status_code


def handle_validation_error(error: ValidationError) -> tuple:
    """Handle validation errors"""
    err = ErrorResponse(
        message=error.message,
        error_code="VALIDATION_ERROR",
        status_code=error.status_code,
    )
    return jsonify(err.to_dict()), err.status_code


def handle_not_found_error(error: NotFoundError) -> tuple:
    """Handle not found errors"""
    err = ErrorResponse(
        message=error.message,
        error_code="NOT_FOUND",
        status_code=error.status_code,
    )
    return jsonify(err.to_dict()), err.status_code


def handle_conflict_error(error: ConflictError) -> tuple:
    """Handle conflict errors (e.g., insufficient stock)"""
    err = ErrorResponse(
        message=error.message,
        error_code="CONFLICT",
        status_code=error.status_code,
    )
    return jsonify(err.to_dict()), err.status_code


def handle_app_error(error: AppError) -> tuple:
    """Handle general application errors"""
    err = ErrorResponse(
        message=error.message,
        error_code="APPLICATION_ERROR",
        status_code=error.status_code,
    )
    return jsonify(err.to_dict()), err.status_code


def handle_generic_error(error: Exception) -> tuple:
    """Handle unexpected errors"""
    err = ErrorResponse(
        message="An unexpected error occurred. Please contact support.",
        error_code="INTERNAL_SERVER_ERROR",
        status_code=500,
        details={"error_type": error.__class__.__name__}
    )
    return jsonify(err.to_dict()), err.status_code
