from app.config import settings
from app.clients.base import http_request, OrchestrationError
from utils.exceptions import AppError, ConflictError, NotFoundError


def get_clinical_record(record_id: int, required: bool = True) -> dict | None:
    """
    Fetch clinical record from clinical records service.
    
    Args:
        record_id: The clinical record ID
        required: If True, raises errors when record not found or service unavailable.
                  If False, returns None on errors.
    
    Returns:
        dict with: recordId, patientId, date, visitNotes, isClosed
        or None if not required and an error occurred
    
    Raises:
        NotFoundError: If required and record not found
        ConflictError: If record is closed
        AppError: If required and service unavailable
    """
    if not settings.CLINICAL_RECORDS_URL:
        if required:
            raise AppError("Clinical records URL is not configured")
        return None

    url = f"{settings.CLINICAL_RECORDS_URL}{settings.CLINICAL_RECORD_VALIDATE_PATH.format(recordId=record_id)}"

    try:
        record = http_request("GET", url)
    except NotFoundError:
        if required:
            raise NotFoundError(f"Clinical record {record_id} not found")
        return None
    except OrchestrationError as e:
        if required:
            raise AppError(f"Clinical record service unavailable: {str(e)}")
        return None
    except Exception as e:
        if required:
            raise AppError(f"Failed to fetch clinical record: {str(e)}")
        return None

    if not isinstance(record, dict):
        raise AppError("Unexpected response format from clinical records service")

    if record.get("isClosed", False):
        raise ConflictError(f"Cannot prescribe for closed clinical record {record_id}")

    return record
