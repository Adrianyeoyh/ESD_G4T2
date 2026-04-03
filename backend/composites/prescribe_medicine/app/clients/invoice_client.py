from app.config import settings
from app.clients.base import http_request


def create_invoice(record_id: int, total_price: str, paid: bool = False) -> dict:
    """
    Create an invoice for a prescription.
    
    Args:
        record_id: The clinical record ID
        total_price: Total price as string
        paid: Payment status (default False)
    
    Returns:
        Created invoice response
    """
    url = f"{settings.INVOICE_SERVICE_URL}/invoice"
    return http_request("POST", url, {
        "recordId": record_id,
        "totalPrice": total_price,
        "paid": paid,
    })
