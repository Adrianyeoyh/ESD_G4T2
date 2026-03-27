from flask import Blueprint

from backend.composites.make_payment.app.controllers.make_payment_controller import handle_payment_event, initiate_payment, retry_payment

make_payment_bp = Blueprint("make_payment_bp", __name__)

make_payment_bp.route("/make_payment/initiate-payment", methods=["POST"])(initiate_payment)
make_payment_bp.route("/make_payment/retry-payment", methods=["POST"])(retry_payment)
make_payment_bp.route("/make_payment/payment-events", methods=["POST"])(handle_payment_event)


