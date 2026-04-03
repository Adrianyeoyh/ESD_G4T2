from app.config import settings
from app.clients.base import http_request, AppError


def create_prescription(record_id: int, drugs: list[dict]) -> dict:
    """
    Create a prescription record with multiple drugs.
    
    Args:
        record_id: The clinical record ID
        drugs: List of dicts with drugId, drugName, quantity
    
    Returns:
        Created prescription response
    """
    service_url = (settings.PRESCRIPTION_SERVICE_URL or "").strip()
    if not service_url:
        raise AppError("Prescription service URL is not configured")

    url = f"{service_url}/prescription"
    return http_request("POST", url, {
        "recordId": record_id,
        "drugs": drugs,
    })


def delete_prescription(prescription_id: int) -> None:
    """Delete a prescription record (for rollback scenarios)."""
    service_url = (settings.PRESCRIPTION_SERVICE_URL or "").strip()
    if not service_url:
        raise AppError("Prescription service URL is not configured")

    url = f"{service_url}/prescription/{prescription_id}"
    http_request("DELETE", url)
