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

invoice_bp = Blueprint("invoice_bp", __name__)


invoice_bp.route("/invoice", methods=["POST"])(create_invoice)
invoice_bp.route("/invoice", methods=["GET"])(list_invoices)
invoice_bp.route("/invoice/<int:invoice_id>", methods=["GET"])(get_invoice)
invoice_bp.route("/invoice/record/<int:record_id>", methods=["GET"])(get_invoice_by_record_id)
invoice_bp.route("/invoice/<int:invoice_id>/payment-pending", methods=["PUT"])(mark_payment_pending)
invoice_bp.route("/invoice/<int:invoice_id>/paid", methods=["PUT"])(mark_paid)
invoice_bp.route("/invoice/<int:invoice_id>/failed", methods=["PUT"])(mark_failed)
invoice_bp.route("/invoice/<int:invoice_id>/retry", methods=["PUT"])(increment_retry)
invoice_bp.route("/invoice/<int:invoice_id>/total", methods=["PUT"])(update_total)
invoice_bp.route("/invoice/<int:invoice_id>", methods=["DELETE"])(delete_invoice)