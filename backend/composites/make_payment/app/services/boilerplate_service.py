import json
import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import pika
import requests

from app.config import settings
from common.tools import InvoiceStatus
from utils.exceptions import AppError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class OrchestrationError(AppError):
    def __init__(self, message: str, error_code: str, status_code: int = 502, extra: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.extra = extra or {}


@dataclass
class ExternalResponseError(Exception):
    status_code: int
    payload: dict


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
        invoice = self._get_invoice(invoice_id)
        self._assert_payable(invoice, flow_type=flow_type)

        payment = self._create_payment_attempt(
            invoice_id=invoice["invoiceId"],
            record_id=invoice["recordId"],
            amount=invoice["total"],
            currency=currency or settings.DEFAULT_CURRENCY,
            description=description,
        )

        try:
            self._mark_invoice_payment_pending(invoice_id=invoice_id)
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
                extra={"invoiceStatus": InvoiceStatus.FAILED.value},
            ) from exc

        return {
            "invoiceId": invoice["invoiceId"],
            "recordId": invoice["recordId"],
            "invoiceStatus": InvoiceStatus.PAYMENT_PENDING.value,
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
            if record_id is not None:
                self._close_record(record_id)
                self._publish_success_notification(record_id, invoice_id, payment_intent_id)
            return {"eventType": event_type, "invoiceStatus": InvoiceStatus.PAID.value}

        if event_type == "payment.failed":
            self._mark_invoice_failed(invoice_id)
            return {"eventType": event_type, "invoiceStatus": InvoiceStatus.FAILED.value}

        if event_type == "payment.cancelled":
            self._mark_invoice_failed(invoice_id)
            return {"eventType": event_type, "invoiceStatus": InvoiceStatus.FAILED.value}

        return {"eventType": event_type, "ignored": True}

    def _assert_payable(self, invoice: dict, flow_type: str):
        status = invoice["status"]
        if flow_type == "retry":
            payable_states = {InvoiceStatus.FAILED.value}
            error_code = "INVOICE_NOT_RETRYABLE"
        else:
            payable_states = {InvoiceStatus.UNPAID.value, InvoiceStatus.FAILED.value}
            error_code = "INVOICE_NOT_PAYABLE"

        if status in payable_states:
            return

        raise OrchestrationError(
            message=f"Invoice {invoice['invoiceId']} is not payable in status {status}",
            error_code=error_code,
            status_code=409,
            extra={"invoiceStatus": status},
        )

    def _get_invoice(self, invoice_id: int) -> dict:
        url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}"
        return self._request("GET", url)

    def _mark_invoice_payment_pending(self, invoice_id: int):
        url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}/payment-pending"
        return self._request("PUT", url)

    def _mark_invoice_paid(self, invoice_id: int):
        url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}/paid"
        return self._request("PUT", url)

    def _mark_invoice_paid_idempotent(self, invoice_id: int):
        invoice = self._get_invoice(invoice_id)
        if invoice["status"] == InvoiceStatus.PAID.value:
            return invoice
        try:
            return self._mark_invoice_paid(invoice_id)
        except OrchestrationError as exc:
            # Handle race where another concurrent webhook already moved it to PAID.
            if exc.status_code == 409:
                latest = self._get_invoice(invoice_id)
                if latest["status"] == InvoiceStatus.PAID.value:
                    return latest
            raise

    def _mark_invoice_failed(self, invoice_id: int):
        url = f"{settings.INVOICE_SERVICE_URL}/invoice/{invoice_id}/failed"
        return self._request("PUT", url)

    def _create_payment_attempt(
        self,
        invoice_id: int,
        record_id: int,
        amount: str | float | Decimal,
        currency: str,
        description: str | None,
    ) -> dict:
        normalized_amount = self._as_decimal_string(amount)
        body = {
            "invoiceId": invoice_id,
            "recordId": record_id,
            "amount": normalized_amount,
            "currency": currency,
        }
        if description:
            body["description"] = description
        url = f"{settings.PAYMENT_SERVICE_URL}/payments/intents"
        return self._request("POST", url, json_body=body)

    def _cancel_payment(self, payment_id: int):
        url = f"{settings.PAYMENT_SERVICE_URL}/payments/{payment_id}/cancel"
        return self._request("POST", url)

    def _close_record(self, record_id: int):
        url = f"{settings.RECORDS_SERVICE_URL}/records/{record_id}/close"
        try:
            response = requests.post(url, timeout=settings.HTTP_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            raise OrchestrationError(
                message=f"Failed to close record {record_id}",
                error_code="RECORDS_CLOSE_FAILED",
                status_code=502,
            ) from exc

        # Treat conflict as already-closed for webhook idempotency.
        if 200 <= response.status_code < 300 or response.status_code == 409:
            return

        raise OrchestrationError(
            message=f"Failed to close record {record_id}",
            error_code="RECORDS_CLOSE_FAILED",
            status_code=502,
            extra={"dependencyStatus": response.status_code},
        )

    def _publish_success_notification(self, record_id: int, invoice_id: int, payment_intent_id: str | None):
        body = {
            "phoneNumber": settings.NOTIFICATION_PHONE_NUMBER,
            "message": (
                f"Payment successful for record {record_id}, invoice {invoice_id}. "
                f"Ref: {payment_intent_id or 'n/a'}."
            ),
        }

        credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=60,
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=settings.RABBITMQ_QUEUE,
            body=json.dumps(body),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()

    def _compensate_payment_and_fail_invoice(self, payment_id: int | None, invoice_id: int, reason: str):
        if payment_id:
            try:
                self._cancel_payment(payment_id)
            except Exception:
                logger.exception("Failed to cancel payment %s during compensation", payment_id)
        try:
            self._mark_invoice_failed(invoice_id)
        except Exception:
            logger.exception("Failed to mark invoice %s as FAILED during compensation", invoice_id)
        logger.error("Compensation executed for invoice %s: %s", invoice_id, reason)

    def _request(self, method: str, url: str, json_body: dict | None = None) -> dict:
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json_body,
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise OrchestrationError(
                message=f"Dependency call failed: {url}",
                error_code="DEPENDENCY_UNREACHABLE",
                status_code=503,
            ) from exc

        if 200 <= response.status_code < 300:
            if response.content:
                return response.json()
            return {}

        payload = {}
        try:
            payload = response.json()
        except ValueError:
            payload = {"error": response.text}

        if response.status_code == 404:
            raise NotFoundError(payload.get("error") or payload.get("message") or "Resource not found")

        if response.status_code in (400, 409):
            raise OrchestrationError(
                message=payload.get("error") or payload.get("message") or "Dependency rejected request",
                error_code="DEPENDENCY_VALIDATION_FAILED",
                status_code=response.status_code,
                extra={"dependencyPayload": payload},
            )

        raise ExternalResponseError(status_code=response.status_code, payload=payload)

    @staticmethod
    def _as_decimal_string(raw_amount: str | float | Decimal) -> str:
        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, TypeError):
            raise ValidationError("amount is invalid")
        if amount <= 0:
            raise ValidationError("amount must be greater than 0")
        return str(amount.quantize(Decimal("0.01")))
