from flask import Blueprint

from app.controllers.payment_controller import (
    create_payment_intent,
    get_payment,
    list_payments_by_invoice,
    get_latest_payment_by_invoice,
    cancel_payment,
    handle_webhook,
)

payment_bp = Blueprint("payment_bp", __name__)

payment_bp.route("/payments/intents", methods=["POST"])(create_payment_intent)
payment_bp.route("/payments/<int:payment_id>", methods=["GET"])(get_payment)
payment_bp.route("/payments/invoice/<int:invoice_id>", methods=["GET"])(list_payments_by_invoice)
payment_bp.route("/payments/invoice/<int:invoice_id>/latest", methods=["GET"])(get_latest_payment_by_invoice)
payment_bp.route("/payments/<int:payment_id>/cancel", methods=["POST"])(cancel_payment)
payment_bp.route("/payments/webhook", methods=["POST"])(handle_webhook)