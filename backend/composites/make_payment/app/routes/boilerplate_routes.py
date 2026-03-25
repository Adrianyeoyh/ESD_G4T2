from flask import Blueprint

from app.controllers.boilerplate_controller import handle_payment_event, initiate_payment, retry_payment

billing_bp = Blueprint("billing_bp", __name__)

billing_bp.route("/billing/initiate-payment", methods=["POST"])(initiate_payment)
billing_bp.route("/billing/retry-payment", methods=["POST"])(retry_payment)
billing_bp.route("/billing/payment-events", methods=["POST"])(handle_payment_event)
