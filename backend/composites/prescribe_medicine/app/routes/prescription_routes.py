from flask import Blueprint, jsonify, request

prescribe_medicine_bp = Blueprint("prescribe_medicine_bp", __name__)


@prescribe_medicine_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@prescribe_medicine_bp.route("/prescribe", methods=["POST"])
def prescribe():
    payload = request.get_json(silent=True) or {}
    return jsonify({"success": True, "data": payload, "error": None}), 201
