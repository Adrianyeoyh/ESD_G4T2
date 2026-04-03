from datetime import datetime

import requests

from app.config import settings
from app.clients.base import OrchestrationError


def get_record(record_id: int) -> dict:
    paths = [f"/Record/{record_id}", f"/record/{record_id}"]
    response = _request_with_fallback("GET", paths)
    return _parse_json_response(response, "Failed to parse record response")


def close_record(record_id: int) -> int:
    record = get_record(record_id)
    if bool(record.get("isClosed")):
        return int(record.get("Id") or record.get("id") or record_id)

    payload = _build_close_record_payload(record, record_id)

    # OutSystems POST /Record returns a raw integer response body.
    response = _request_with_fallback("POST", ["/Record"], json_body=payload)
    return _parse_int_text_response(response, "Invalid close-record response")


def _request_with_fallback(method: str, paths: list[str], json_body: dict | None = None) -> requests.Response:
    last_error = None
    for path in paths:
        try:
            response = requests.request(
                method=method,
                url=f"{settings.RECORDS_SERVICE_URL.rstrip('/')}{path}",
                json=json_body,
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            last_error = exc
            continue

        if response.status_code == 404:
            continue

        if response.status_code >= 400:
            raise OrchestrationError(
                message=f"Records API rejected request with status {response.status_code}",
                error_code="RECORDS_API_ERROR",
                status_code=502,
                extra={"dependencyStatus": response.status_code, "dependencyBody": response.text},
            )

        return response

    if last_error:
        raise OrchestrationError(
            message=f"Records API unreachable: {last_error}",
            error_code="RECORDS_API_UNREACHABLE",
            status_code=503,
        ) from last_error

    raise OrchestrationError(
        message="Record endpoint not found",
        error_code="RECORD_NOT_FOUND",
        status_code=404,
    )


def _parse_json_response(response: requests.Response, error_message: str) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise OrchestrationError(
            message=error_message,
            error_code="RECORDS_API_BAD_RESPONSE",
            status_code=502,
            extra={"responseText": response.text},
        ) from exc
    if not isinstance(payload, dict):
        raise OrchestrationError(
            message="Records API returned a non-object payload",
            error_code="RECORDS_API_BAD_RESPONSE",
            status_code=502,
            extra={"responseBody": payload},
        )
    return payload


def _parse_int_text_response(response: requests.Response, error_message: str) -> int:
    raw = (response.text or "").strip()
    try:
        return int(raw)
    except ValueError as exc:
        raise OrchestrationError(
            message=error_message,
            error_code="RECORDS_API_BAD_RESPONSE",
            status_code=502,
            extra={"responseText": raw},
        ) from exc


def _normalize_record_dates(payload: dict) -> None:
    for key in ("VisitDate", "visitDate"):
        if key not in payload or not payload[key]:
            continue
        payload[key] = _to_yyyy_mm_dd(payload[key])


def _build_close_record_payload(record: dict, record_id: int) -> dict:
    resolved_id = int(record.get("Id") or record.get("id") or record_id)
    resolved_patient_id = record.get("patientId") or record.get("PatientId")
    if resolved_patient_id is None:
        raise OrchestrationError(
            message=f"Record {resolved_id} has no patientId",
            error_code="MISSING_PATIENT_ID",
            status_code=502,
        )

    resolved_date = (
        record.get("date")
        or record.get("Date")
        or record.get("visitDate")
        or record.get("VisitDate")
        or ""
    )

    resolved_visit_notes = (
        record.get("VisitNotes")
        or record.get("visitNotes")
        or record.get("notes")
        or ""
    )

    return {
        "Id": resolved_id,
        "patientId": str(resolved_patient_id).strip(),
        "date": _to_yyyy_mm_dd(resolved_date),
        "VisitNotes": str(resolved_visit_notes),
        "isClosed": True,
    }


def _to_yyyy_mm_dd(raw: str) -> str:
    text = str(raw).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.date().isoformat()
    except ValueError:
        return text[:10]
