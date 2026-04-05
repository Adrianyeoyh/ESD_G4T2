from flask import Blueprint

from app.controllers.prescription_controller import prescribe_medicine

prescribe_medicine_bp = Blueprint("prescribe_medicine_bp", __name__)


@prescribe_medicine_bp.route("/prescribe/<int:record_id>", methods=["POST"])
def prescribe(record_id):
    return prescribe_medicine(record_id)