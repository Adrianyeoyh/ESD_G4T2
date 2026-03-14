from flask import Blueprint
from app.controllers import invoice_controller

invoice_bp = Blueprint("invoice_bp", __name__)

invoice_bp.route("/invoice", methods=["POST"])(invoice_controller.create_invoice)
invoice_bp.route("/invoice/record/<int:record_id>", methods=["GET"])(invoice_controller.get_invoice_by_record)