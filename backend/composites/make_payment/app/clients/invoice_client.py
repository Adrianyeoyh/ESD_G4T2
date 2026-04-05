from app.clients.base import http_request
from app.config import settings


def create_invoice(record_id: int, total: str | float) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice"
    return http_request("POST", url, json_body={"recordId": int(record_id), "total": total})


def get_invoice_by_record_id(record_id: int) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice/record/{int(record_id)}"
    return http_request("GET", url)


def mark_payment_pending(invoice_id: int) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice/{int(invoice_id)}/payment-pending"
    return http_request("PUT", url)


def mark_paid(invoice_id: int) -> dict:
    url = f"{settings.INVOICE_SERVICE_URL}/invoice/{int(invoice_id)}/paid"
    return http_request("PUT", url)
