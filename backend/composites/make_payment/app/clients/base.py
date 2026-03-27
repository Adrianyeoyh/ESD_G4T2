import logging

import requests
from flask import g, has_request_context

from app.config import settings
from utils.exceptions import AppError, NotFoundError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Orchestrator-specific exceptions (raised by client helpers, handled by the
# controller error-handler layer).
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Shared HTTP helper — every client module delegates here.
# ---------------------------------------------------------------------------

def _get_correlation_id() -> str | None:
    if has_request_context():
        return getattr(g, "correlation_id", None)
    return None


def http_request(method: str, url: str, json_body: dict | None = None) -> dict:
    """Make an HTTP request to a downstream microservice.

    Returns the parsed JSON body on 2xx.
    Raises OrchestrationError on 400/409, NotFoundError on 404,
    ExternalResponseError on anything else.
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

    if response.status_code == 404:
        raise NotFoundError(payload.get("error") or payload.get("message") or "Resource not found")

    if response.status_code in (400, 409):
        raise OrchestrationError(
            message=payload.get("error") or payload.get("message") or "Dependency rejected request",
            error_code="DEPENDENCY_VALIDATION_FAILED",
            status_code=response.status_code,
            extra={"dependencyPayload": payload},
        )

    raise ExternalResponseError(status_code=response.status_code, payload=payload)
