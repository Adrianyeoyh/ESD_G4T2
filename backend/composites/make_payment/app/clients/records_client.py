from app.config import settings
from app.clients.base import http_request, OrchestrationError


def get_record(record_id: int) -> dict:
    url = f"{settings.RECORDS_SERVICE_URL}/record/{record_id}"
    return http_request("GET", url)


def close_record(record_id: int) -> None:
    url = f"{settings.RECORDS_SERVICE_URL}/records/{record_id}/close"
    try:
        http_request("POST", url)
    except OrchestrationError as exc:
        # 409 means already closed — idempotent success for webhook replays.
        if exc.status_code == 409:
            return
        raise
