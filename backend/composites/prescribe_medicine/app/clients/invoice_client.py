from app.config import settings
from app.clients.base import http_request


def create_invoice(record_id: int, total: str) -> dict:
    """Create an invoice for a prescription."""
    url = f"{settings.INVOICE_SERVICE_URL}/invoice"
    return http_request("POST", url, {
        "recordId": record_id,
        "total": total,
    })
