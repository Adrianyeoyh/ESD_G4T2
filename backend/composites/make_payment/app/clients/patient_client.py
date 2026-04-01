import requests

from app.clients.base import OrchestrationError
from app.config import settings


def get_patient(patient_id: int) -> dict:
    paths = [f"/patient/{patient_id}", f"/Patient/{patient_id}"]
    response = _request_with_fallback(paths)
    try:
        payload = response.json()
    except ValueError as exc:
        raise OrchestrationError(
            message="Patient API returned invalid JSON",
            error_code="PATIENT_API_BAD_RESPONSE",
            status_code=502,
            extra={"responseText": response.text},
        ) from exc

    if not isinstance(payload, dict):
        raise OrchestrationError(
            message="Patient API returned a non-object payload",
            error_code="PATIENT_API_BAD_RESPONSE",
            status_code=502,
            extra={"responseBody": payload},
        )
    return payload


def _request_with_fallback(paths: list[str]) -> requests.Response:
    last_error = None
    for path in paths:
        try:
            response = requests.get(
                f"{settings.PATIENT_SERVICE_URL.rstrip('/')}{path}",
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            last_error = exc
            continue

        if response.status_code == 404:
            continue
        if response.status_code >= 400:
            raise OrchestrationError(
                message=f"Patient API rejected request with status {response.status_code}",
                error_code="PATIENT_API_ERROR",
                status_code=502,
                extra={"dependencyStatus": response.status_code, "dependencyBody": response.text},
            )
        return response

    if last_error:
        raise OrchestrationError(
            message=f"Patient API unreachable: {last_error}",
            error_code="PATIENT_API_UNREACHABLE",
            status_code=503,
        ) from last_error

    raise OrchestrationError(
        message="Patient endpoint not found",
        error_code="PATIENT_NOT_FOUND",
        status_code=404,
    )
