from app.config import settings
from app.clients.base import http_request, AppError


def create_prescription(record_id: int, drug_id: int, quantity: int, dosage: str) -> dict:
    """Create a prescription record."""
    service_url = (settings.PRESCRIPTION_SERVICE_URL or "").strip()
    if not service_url:
        raise AppError("Prescription service URL is not configured")

    url = f"{service_url}/prescription"
    return http_request("POST", url, {
        "recordId": record_id,
        "drugId": drug_id,
        "quantity": quantity,
        "dosage": dosage,
    })


def delete_prescription(prescription_id: int) -> None:
    """Delete a prescription record (for rollback scenarios)."""
    service_url = (settings.PRESCRIPTION_SERVICE_URL or "").strip()
    if not service_url:
        raise AppError("Prescription service URL is not configured")

    url = f"{service_url}/prescription/{prescription_id}"
    http_request("DELETE", url)
