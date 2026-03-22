from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
import stripe

from app.services.payment_service import PaymentService
from app.services import webhook_service
from utils.exceptions import AppError, ValidationError

service = PaymentService()


def serialize_payment(payment):
    return {
        "paymentId": payment.payment_id,
        "invoiceId": payment.invoice_id,
        "recordId": payment.record_id,
        "provider": payment.provider,
        "paymentIntentId": payment.payment_intent_id,
        "clientSecret": payment.client_secret,
        "attemptNumber": payment.attempt_number,
        "status": payment.status.value,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "errorCode": payment.error_code,
        "errorMessage": payment.error_message,
        "paidAt": payment.paid_at.isoformat() if payment.paid_at else None,
        "cancelledAt": payment.cancelled_at.isoformat() if payment.cancelled_at else None,
        "createdAt": payment.created_at.isoformat() if payment.created_at else None,
        "updatedAt": payment.updated_at.isoformat() if payment.updated_at else None,
    }


def create_payment_intent():
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        for field in ("invoiceId", "recordId", "amount", "currency"):
            if field not in data:
                raise ValidationError(f"{field} is required")

        payment = service.create_payment_attempt(
            invoice_id=data["invoiceId"],
            record_id=data["recordId"],
            amount=data["amount"],
            currency=data["currency"],
            description=data.get("description"),
        )

        return jsonify({
            "success": True,
            "data": serialize_payment(payment),
            "error": None,
        }), 201

    except AppError as e:
        return jsonify({"success": False, "data": None, "error": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"success": False, "data": None, "error": "Database error"}), 500
    except Exception:
        return jsonify({"success": False, "data": None, "error": "Internal server error"}), 500


def get_payment(payment_id):
    try:
        payment = service.get_payment(payment_id)
        return jsonify({"success": True, "data": serialize_payment(payment), "error": None}), 200

    except AppError as e:
        return jsonify({"success": False, "data": None, "error": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"success": False, "data": None, "error": "Database error"}), 500
    except Exception:
        return jsonify({"success": False, "data": None, "error": "Internal server error"}), 500


def list_payments_by_invoice(invoice_id):
    try:
        payments = service.list_payments_by_invoice_id(invoice_id)
        return jsonify({
            "success": True,
            "data": [serialize_payment(p) for p in payments],
            "error": None,
        }), 200

    except AppError as e:
        return jsonify({"success": False, "data": None, "error": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"success": False, "data": None, "error": "Database error"}), 500
    except Exception:
        return jsonify({"success": False, "data": None, "error": "Internal server error"}), 500


def get_latest_payment_by_invoice(invoice_id):
    try:
        payment = service.get_latest_payment_by_invoice_id(invoice_id)
        return jsonify({"success": True, "data": serialize_payment(payment), "error": None}), 200

    except AppError as e:
        return jsonify({"success": False, "data": None, "error": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"success": False, "data": None, "error": "Database error"}), 500
    except Exception:
        return jsonify({"success": False, "data": None, "error": "Internal server error"}), 500


def cancel_payment(payment_id):
    try:
        payment = service.mark_cancelled(payment_id)
        return jsonify({"success": True, "data": serialize_payment(payment), "error": None}), 200

    except AppError as e:
        return jsonify({"success": False, "data": None, "error": e.message}), e.status_code
    except SQLAlchemyError:
        return jsonify({"success": False, "data": None, "error": "Database error"}), 500
    except Exception:
        return jsonify({"success": False, "data": None, "error": "Internal server error"}), 500


def handle_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        webhook_service.handle_webhook_event(payload, sig_header)
        return jsonify({"received": True}), 200

    except stripe.error.SignatureVerificationError:
        return jsonify({"success": False, "error": "Invalid Stripe signature"}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid webhook payload"}), 400
    except SQLAlchemyError:
        return jsonify({"success": False, "error": "Database error"}), 500
    except Exception:
        return jsonify({"success": False, "error": "Internal server error"}), 500