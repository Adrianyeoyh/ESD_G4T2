import logging

import requests
from flask import g, has_request_context

from app.config import settings
from utils.exceptions import AppError, ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class OrchestrationError(AppError):
    """A downstream service rejected the request or is unreachable."""

    def __init__(self, message: str, error_code: str, status_code: int = 502, extra: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.extra = extra or {}


class ExternalResponseError(AppError):
    """Unexpected HTTP status from a dependency (not 2xx, 400, 404, or 409)."""

    def __init__(self, status_code: int, payload: dict):
        super().__init__("Unexpected dependency response")
        self.status_code = status_code
        self.payload = payload


def _get_correlation_id() -> str | None:
    if has_request_context():
        return getattr(g, "correlation_id", None)
    return None


def _extract_error_message(payload: dict, fallback: str) -> str:
    """Extract error message from response payload."""
    if isinstance(payload, dict):
        error_field = payload.get("error")
        if isinstance(error_field, dict):
            return (
                error_field.get("message")
                or error_field.get("detail")
                or str(error_field)
            )
        elif error_field is not None:
            return str(error_field)
        return (
            payload.get("message")
            or payload.get("detail")
            or fallback
        )
    return fallback


def http_request(method: str, url: str, json_body: dict | None = None) -> dict:
    """Make an HTTP request to a downstream microservice.

    Returns the parsed JSON body on 2xx.
    Raises appropriate exceptions based on status code.
    """
    headers = {}
    correlation_id = _get_correlation_id()
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_body,
            headers=headers,
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise OrchestrationError(
            message=f"Dependency call failed: {url}",
            error_code="DEPENDENCY_UNREACHABLE",
            status_code=503,
        ) from exc

    if 200 <= response.status_code < 300:
        if response.content:
            return response.json()
        return {}

    payload = {}
    try:
        payload = response.json()
    except ValueError:
        payload = {"error": response.text}

    message = _extract_error_message(payload, "Downstream service error")

    if response.status_code == 400:
        raise ValidationError(message)

    if response.status_code == 404:
        raise NotFoundError(message)

    if response.status_code == 409:
        raise ConflictError(message)

    raise ExternalResponseError(status_code=response.status_code, payload=payload)
