import logging

from app.clients import invoice_client, payment_client, records_client, notification_client, patient_client
from app.clients.base import OrchestrationError
from app.config import settings
from utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class MakePaymentService:
    def initiate_payment(self, invoice_id: int, currency: str | None = None, description: str | None = None):
        return self._start_payment(
            invoice_id=invoice_id,
            currency=currency,
            description=description,
            flow_type="initiate",
        )

    def retry_payment(self, invoice_id: int, currency: str | None = None, description: str | None = None):
        return self._start_payment(
            invoice_id=invoice_id,
            currency=currency,
            description=description,
            flow_type="retry",
        )

    def _start_payment(
        self,
        invoice_id: int,
        currency: str | None,
        description: str | None,
        flow_type: str,
    ):
        invoice = invoice_client.get_invoice(invoice_id)
        self._assert_payable(invoice, flow_type=flow_type)

        payment = payment_client.create_payment_attempt(
            invoice_id=invoice["invoiceId"],
            record_id=invoice["recordId"],
            amount=invoice["total"],
            currency=currency or settings.DEFAULT_CURRENCY,
            description=description,
        )

        try:
            invoice_client.mark_payment_pending(invoice_id=invoice_id)
        except Exception as exc:
            self._compensate_payment_and_fail_invoice(
                payment_id=payment.get("paymentId"),
                invoice_id=invoice_id,
                reason=f"Failed to mark invoice as PAYMENT_PENDING: {str(exc)}",
            )
            raise OrchestrationError(
                message="Payment was created but invoice state update failed",
                error_code="ORCHESTRATION_STATE_INCONSISTENT",
                status_code=502,
                extra={"invoiceStatus": "failed"},
            ) from exc

        return {
            "invoiceId": invoice["invoiceId"],
            "recordId": invoice["recordId"],
            "invoiceStatus": "payment_pending",
            "paymentId": payment["paymentId"],
            "paymentIntentId": payment["paymentIntentId"],
            "attemptNumber": payment["attemptNumber"],
            "clientSecret": payment["clientSecret"],
        }

    def handle_payment_event(self, payload: dict):
        event_type = payload.get("eventType")
        if not event_type:
            raise ValidationError("eventType is required")

        invoice_id = payload.get("invoiceId")
        record_id = payload.get("recordId")
        payment_intent_id = payload.get("paymentIntentId")

        if not invoice_id:
            raise ValidationError("invoiceId is required")

        if event_type == "payment.succeeded":
            self._mark_invoice_paid_idempotent(invoice_id)
            notification_status = "skipped"
            if record_id is not None:
                records_client.close_record(record_id)
                try:
                    phone_number = self._get_patient_phone(record_id)
                    notification_client.publish_success_notification(
                        record_id, invoice_id, payment_intent_id, phone_number,
                    )
                    notification_status = "queued"
                except Exception:
                    logger.exception("Non-critical: failed to publish notification for invoice %s", invoice_id)
                    notification_status = "failed"
            return {"eventType": event_type, "invoiceStatus": "paid", "notificationStatus": notification_status}

        if event_type == "payment.failed":
            invoice_client.mark_failed(invoice_id)
            return {"eventType": event_type, "invoiceStatus": "failed"}

        if event_type == "payment.cancelled":
            invoice_client.mark_failed(invoice_id)
            return {"eventType": event_type, "invoiceStatus": "failed"}

        return {"eventType": event_type, "ignored": True}

    def _assert_payable(self, invoice: dict, flow_type: str):
        status = invoice["status"]
        if flow_type == "retry":
            payable_states = {"failed"}
            error_code = "INVOICE_NOT_RETRYABLE"
        else:
            payable_states = {"draft", "failed"}
            error_code = "INVOICE_NOT_PAYABLE"

        if status in payable_states:
            return

        raise OrchestrationError(
            message=f"Invoice {invoice['invoiceId']} is not payable in status {status}",
            error_code=error_code,
            status_code=409,
            extra={"invoiceStatus": status},
        )

    def _mark_invoice_paid_idempotent(self, invoice_id: int):
        invoice = invoice_client.get_invoice(invoice_id)
        if invoice["status"] == "paid":
            return invoice
        try:
            return invoice_client.mark_paid(invoice_id)
        except OrchestrationError as exc:
            # Handle race where another concurrent webhook already moved it to PAID.
            if exc.status_code == 409:
                latest = invoice_client.get_invoice(invoice_id)
                if latest["status"] == "paid":
                    return latest
            raise

    def _get_patient_phone(self, record_id: int) -> str:
        record = records_client.get_record(record_id)
        patient_id = record.get("patientId") or record.get("PatientId")
        if not patient_id:
            raise OrchestrationError(
                message=f"Record {record_id} has no patientId",
                error_code="MISSING_PATIENT_ID",
                status_code=502,
            )
        patient = patient_client.get_patient(patient_id)
        phone_no = patient.get("phoneNo") or patient.get("PhoneNo")
        if not phone_no:
            raise OrchestrationError(
                message=f"Patient {patient_id} has no phone number",
                error_code="MISSING_PHONE_NUMBER",
                status_code=502,
            )
        return f"+65{phone_no}"

    def _compensate_payment_and_fail_invoice(self, payment_id: int | None, invoice_id: int, reason: str):
        if payment_id:
            try:
                payment_client.cancel_payment(payment_id)
            except Exception:
                logger.exception("Failed to cancel payment %s during compensation", payment_id)
        try:
            invoice = invoice_client.get_invoice(invoice_id)
            status = invoice.get("status")
            if status == "payment_pending":
                invoice_client.mark_failed(invoice_id)
            elif status == "draft":
                # DRAFT→FAILED is not allowed; DRAFT→CANCELLED is.
                invoice_client.mark_cancelled(invoice_id)
            # If already failed/cancelled/paid, no action needed.
        except Exception:
            logger.exception("Failed to compensate invoice %s (may need manual review)", invoice_id)
        logger.error("Compensation executed for invoice %s: %s", invoice_id, reason)
