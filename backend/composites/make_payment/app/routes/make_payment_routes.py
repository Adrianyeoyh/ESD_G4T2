from flask import Blueprint, jsonify

from app.controllers.make_payment_controller import initiate_payment

make_payment_bp = Blueprint("make_payment_bp", __name__)

make_payment_bp.route("/make_payment/initiate-payment", methods=["POST"])(initiate_payment)


@make_payment_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


