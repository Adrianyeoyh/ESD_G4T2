from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repositories.invoice_repository import InvoiceRepository
from utils.exceptions import NotFoundError, ConflictError, AppError
from common.tools import InvoiceStatus


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InvoiceRepository(db)

    def create_invoice(self, record_id: int, total: float):
        existing = self.repo.get_by_record_id(record_id)
        if existing:
            raise ConflictError("Invoice already exists for this record")

        invoice = self.repo.create(record_id, total)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_invoice(self, invoice_id: int):
        invoice = self.repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")
        return invoice

    def get_invoice_by_record_id(self, record_id: int):
        invoice = self.repo.get_by_record_id(record_id)
        if not invoice:
            raise NotFoundError("Invoice not found for this record")
        return invoice

    def list_invoices(self):
        return self.repo.list_all()

    def mark_payment_pending(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)

        if invoice.status == InvoiceStatus.PAID:
            raise ConflictError("Invoice is already paid")

        invoice.status = InvoiceStatus.PAYMENT_PENDING
        self.repo.save(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def mark_paid(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)
        invoice.status = InvoiceStatus.PAID
        self.repo.save(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def mark_failed(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)
        invoice.status = InvoiceStatus.FAILED
        self.repo.save(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def mark_cancelled(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)
        invoice.status = InvoiceStatus.CANCELLED
        self.repo.save(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def update_total(self, invoice_id: int, new_total: float):
        invoice = self.get_invoice(invoice_id)
        invoice.total = new_total
        self.repo.save(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def delete_invoice(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)

        if invoice.status == InvoiceStatus.PAID:
            raise ConflictError("Cannot delete a paid invoice")

        self.repo.delete(invoice)
        self.db.commit()