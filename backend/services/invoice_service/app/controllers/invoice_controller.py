from flask import request, jsonify
from app.services.invoice_service import InvoiceService

service = InvoiceService()

def create_invoice():
    data = request.get_json()
    invoice = service.create_invoice(
        record_id=data["recordId"],
        total=data["total"]
    )
    return jsonify({
        "invoiceId": invoice.invoice_id,
        "recordId": invoice.record_id,
        "total": float(invoice.total),
        "paid": invoice.paid,
        "status": invoice.status
    }), 201

def get_invoice_by_record(record_id):
    invoice = service.get_invoice_by_record(record_id)
    if not invoice:
        return jsonify({"message": "Invoice not found"}), 404

    return jsonify({
        "invoiceId": invoice.invoice_id,
        "recordId": invoice.record_id,
        "total": float(invoice.total),
        "paid": invoice.paid,
        "status": invoice.status,
        "retryCount": invoice.retry_count
    }), 200