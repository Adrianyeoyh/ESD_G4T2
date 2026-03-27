import requests

from app.config import settings
from app.clients.base import http_request, OrchestrationError


def get_record(record_id: int) -> dict:
    url = f"{settings.RECORDS_SERVICE_URL}/record/{record_id}"
    return http_request("GET", url)


def close_record(record_id: int) -> None:
    url = f"{settings.RECORDS_SERVICE_URL}/records/{record_id}/close"
    try:
        response = requests.post(url, timeout=settings.HTTP_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise OrchestrationError(
            message=f"Failed to close record {record_id}",
            error_code="RECORDS_CLOSE_FAILED",
            status_code=502,
        ) from exc

    # Treat 409 as already-closed for webhook idempotency.
    if 200 <= response.status_code < 300 or response.status_code == 409:
        return

    raise OrchestrationError(
        message=f"Failed to close record {record_id}",
        error_code="RECORDS_CLOSE_FAILED",
        status_code=502,
        extra={"dependencyStatus": response.status_code},
    )
