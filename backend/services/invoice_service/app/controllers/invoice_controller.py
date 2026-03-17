from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from app.services.invoice_service import InvoiceService
from shared.utils.exceptions import AppError, ValidationError

service = InvoiceService()


def serialize_invoice(invoice):
    return {
        "invoiceId": invoice.invoice_id,
        "recordId": invoice.record_id,
        "total": float(invoice.total),
        "status": invoice.status.value,
        "paymentIntentId": invoice.payment_intent_id,
        "retryCount": invoice.retry_count,
        "lastPaymentError": invoice.last_payment_error,
        "createdAt": invoice.created_at.isoformat() if invoice.created_at else None,
        "updatedAt": invoice.updated_at.isoformat() if invoice.updated_at else None,
    }


def create_invoice():
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        if "recordId" not in data:
            raise ValidationError("recordId is required")

        if "total" not in data:
            raise ValidationError("total is required")

        invoice = service.create_invoice(
            record_id=data["recordId"],
            total=data["total"]
        )

        return jsonify(serialize_invoice(invoice)), 201

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def get_invoice(invoice_id):
    try:
        invoice = service.get_invoice(invoice_id)
        return jsonify(serialize_invoice(invoice)), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def get_invoice_by_record_id(record_id):
    try:
        invoice = service.get_invoice_by_record_id(record_id)
        return jsonify(serialize_invoice(invoice)), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def list_invoices():
    try:
        invoices = service.list_invoices()
        return jsonify([serialize_invoice(invoice) for invoice in invoices]), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def mark_payment_pending(invoice_id):
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        if "paymentIntentId" not in data:
            raise ValidationError("paymentIntentId is required")

        invoice = service.mark_payment_pending(
            invoice_id=invoice_id,
            payment_intent_id=data["paymentIntentId"]
        )

        return jsonify(serialize_invoice(invoice)), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def mark_paid(invoice_id):
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        if "paymentIntentId" not in data:
            raise ValidationError("paymentIntentId is required")

        invoice = service.mark_paid(
            invoice_id=invoice_id,
            payment_intent_id=data["paymentIntentId"]
        )

        return jsonify(serialize_invoice(invoice)), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def mark_failed(invoice_id):
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        if "errorMessage" not in data:
            raise ValidationError("errorMessage is required")

        invoice = service.mark_failed(
            invoice_id=invoice_id,
            error_message=data["errorMessage"]
        )

        return jsonify(serialize_invoice(invoice)), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def increment_retry(invoice_id):
    try:
        data = request.get_json(silent=True) or {}

        invoice = service.increment_retry(
            invoice_id=invoice_id,
            error_message=data.get("errorMessage")
        )

        return jsonify(serialize_invoice(invoice)), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def update_total(invoice_id):
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        if "total" not in data:
            raise ValidationError("total is required")

        invoice = service.update_total(
            invoice_id=invoice_id,
            total=data["total"]
        )

        return jsonify(serialize_invoice(invoice)), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


def delete_invoice(invoice_id):
    try:
        service.delete_invoice(invoice_id)
        return jsonify({"message": "Invoice deleted successfully"}), 200

    except AppError as e:
        return jsonify({"message": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"message": "Database error"}), 500
    except Exception:
        return jsonify({"message": "Internal server error"}), 500