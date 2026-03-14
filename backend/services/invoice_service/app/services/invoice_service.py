from app.repositories.invoice_repository import InvoiceRepository

class InvoiceService:
    def __init__(self):
        self.repo = InvoiceRepository()

    def create_invoice(self, record_id: int, total: float):
        existing = self.repo.get_by_record_id(record_id)
        if existing:
            return existing
        return self.repo.create(record_id, total)

    def get_invoice(self, invoice_id: int):
        return self.repo.get_by_id(invoice_id)

    def get_invoice_by_record(self, record_id: int):
        return self.repo.get_by_record_id(record_id)

    def attach_payment_intent(self, invoice_id: int, payment_intent_id: str):
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        invoice.payment_intent_id = payment_intent_id
        invoice.status = "PAYMENT_IN_PROGRESS"
        return self.repo.save(invoice)

    def mark_paid(self, invoice_id: int, payment_intent_id: str):
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        invoice.paid = True
        invoice.status = "PAID"
        invoice.payment_intent_id = payment_intent_id
        return self.repo.save(invoice)

    def mark_failed(self, invoice_id: int, payment_intent_id: str, error: str):
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        invoice.status = "PAYMENT_FAILED"
        invoice.payment_intent_id = payment_intent_id
        invoice.retry_count += 1
        invoice.last_payment_error = error
        return self.repo.save(invoice)