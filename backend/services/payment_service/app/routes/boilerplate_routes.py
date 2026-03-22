from flask import Blueprint

from backend.services.boilerplate_service.app.controllers.boilerplate_controller import (
    create_invoice,
    get_invoice,
    get_invoice_by_record_id,
    list_invoices,
    mark_payment_pending,
    mark_paid,
    mark_failed,
    increment_retry,
    update_total,
    delete_invoice,
)

payment_bp = Blueprint("payment_bp", __name__)


payment_bp.route("payments/intent", methods=["POST"]) ()
payment_bp.route("payments/<int:payment_id>", methods=["GET"]) ()
payment_bp.route("/payments/intent/<payment_intent_id>", methods=["GET"]) ()
payment_bp.route("/payments/webhook", methods=["POST"]) ()
payment_bp.route("//payments/retry", methods=["POST"]) ()