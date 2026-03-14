from app.config.db import SessionLocal
from app.models.invoice_model import Invoice

class InvoiceRepository:
    def create(self, record_id: int, total: float) -> Invoice:
        db = SessionLocal()
        try:
            invoice = Invoice(record_id=record_id, total=total)
            db.add(invoice)
            db.commit()
            db.refresh(invoice)
            return invoice
        finally:
            db.close()

    def get_by_id(self, invoice_id: int):
        db = SessionLocal()
        try:
            return db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
        finally:
            db.close()

    def get_by_record_id(self, record_id: int):
        db = SessionLocal()
        try:
            return db.query(Invoice).filter(Invoice.record_id == record_id).first()
        finally:
            db.close()

    def save(self, invoice: Invoice):
        db = SessionLocal()
        try:
            merged = db.merge(invoice)
            db.commit()
            db.refresh(merged)
            return merged
        finally:
            db.close()