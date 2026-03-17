from app.models.invoice_model import Invoice

class InvoiceRepository:
    def __init__(self, db):
        self.db = db

    def create(self, record_id: int, total: float) -> Invoice:
        invoice = Invoice(record_id=record_id, total=total)
        self.db.add(invoice)
        return invoice

    def get_by_id(self, invoice_id: int) -> Invoice | None:
        return (
            self.db.query(Invoice)
            .filter(Invoice.invoice_id == invoice_id)
            .first()
        )

    def get_by_record_id(self, record_id: int) -> Invoice | None:
        return (
            self.db.query(Invoice)
            .filter(Invoice.record_id == record_id)
            .first()
        )

    def list_all(self) -> list[Invoice]:
        return (
            self.db.query(Invoice)
            .order_by(Invoice.created_at.desc())
            .all()
        )

    def save(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        return invoice

    def delete(self, invoice: Invoice) -> None:
        self.db.delete(invoice)