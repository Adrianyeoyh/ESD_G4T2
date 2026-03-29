from app.config import settings
from app.clients.base import http_request


def get_invoice(invoice_id: int) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}"
    return http_request("GET", url)


def mark_payment_pending(invoice_id: int) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}/payment-pending"
    return http_request("PUT", url)


def mark_paid(invoice_id: int) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}/paid"
    return http_request("PUT", url)


def mark_failed(invoice_id: int) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}/failed"
    return http_request("PUT", url)


def mark_cancelled(invoice_id: int) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}/cancelled"
    return http_request("PUT", url)
