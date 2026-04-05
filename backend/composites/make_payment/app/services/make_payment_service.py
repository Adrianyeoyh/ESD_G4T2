from app.clients import invoice_client, payment_client
from app.clients.base import OrchestrationError
from utils.exceptions import NotFoundError


class MakePaymentService:
    """Composite orchestrator for payment + invoice updates."""

    def process_payment(self, nric: str, amount: str | float, record_id: int, payment_method: str) -> dict:
        payment_result = payment_client.process_payment(amount=amount, payment_method=payment_method)
        payment_status = str(payment_result.get("status", "")).lower()
        transaction_id = payment_result.get("transactionId") or payment_result.get("transaction_id")

        if payment_status != "success":
            return {
                "nric": nric,
                "recordId": record_id,
                "paymentStatus": "failed",
                "transactionId": transaction_id,
                "invoiceUpdated": False,
                "invoiceStatus": "unchanged",
            }

        invoice = self._mark_invoice_paid(record_id=record_id, amount=amount)
        return {
            "nric": nric,
            "recordId": record_id,
            "paymentStatus": "success",
            "transactionId": transaction_id,
            "invoiceUpdated": True,
            "invoiceStatus": invoice.get("status", "paid"),
            "invoice": invoice,
        }

    def _mark_invoice_paid(self, record_id: int, amount: str | float) -> dict:
        try:
            invoice = invoice_client.get_invoice_by_record_id(record_id)
        except NotFoundError:
            invoice = invoice_client.create_invoice(record_id=record_id, total=amount)
        except OrchestrationError as exc:
            if exc.status_code != 404:
                raise
            invoice = invoice_client.create_invoice(record_id=record_id, total=amount)

        invoice_id = invoice.get("invoiceId") or invoice.get("invoice_id")
        status = str(invoice.get("status", "")).lower()

        if status in {"draft", "failed"}:
            invoice = invoice_client.mark_payment_pending(invoice_id)
            status = str(invoice.get("status", "")).lower()

        if status == "payment_pending":
            return invoice_client.mark_paid(invoice_id)

        if status == "paid":
            return invoice

        raise OrchestrationError(
            message=f"Invoice is in unsupported status for payment completion: {status}",
            error_code="INVOICE_STATE_INVALID",
            status_code=409,
            extra={"invoice": invoice},
        )
