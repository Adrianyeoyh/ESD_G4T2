import logging
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repositories.invoice_repository import InvoiceRepository
from utils.exceptions import NotFoundError, ConflictError, AppError
from common.tools import InvoiceStatus

logger = logging.getLogger(__name__)


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InvoiceRepository(db)

    def _commit_and_refresh(self, entity):
        try:
            self.db.commit()
            self.db.refresh(entity)
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def create_invoice(self, record_id: int, total: Decimal):
        existing = self.repo.get_by_record_id(record_id)
        if existing:
            raise ConflictError("Invoice already exists for this record")

        invoice = self.repo.create(record_id, total)
        self._commit_and_refresh(invoice)
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

    ALLOWED_TRANSITIONS = {
        InvoiceStatus.DRAFT: {InvoiceStatus.PAYMENT_PENDING, InvoiceStatus.CANCELLED},
        InvoiceStatus.PAYMENT_PENDING: {InvoiceStatus.PAID, InvoiceStatus.FAILED, InvoiceStatus.CANCELLED},
        InvoiceStatus.FAILED: {InvoiceStatus.PAYMENT_PENDING, InvoiceStatus.CANCELLED},
        InvoiceStatus.PAID: set(),
        InvoiceStatus.CANCELLED: set(),
    }

    def _transition(self, invoice, new_status: InvoiceStatus):
        allowed = self.ALLOWED_TRANSITIONS.get(invoice.status, set())
        if new_status not in allowed:
            raise ConflictError(
                f"Cannot transition from {invoice.status.value} to {new_status.value}"
            )
        invoice.status = new_status
        self.repo.save(invoice)
        self._commit_and_refresh(invoice)
        return invoice

    def mark_payment_pending(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)
        return self._transition(invoice, InvoiceStatus.PAYMENT_PENDING)

    def mark_paid(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)
        return self._transition(invoice, InvoiceStatus.PAID)

    def mark_failed(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)
        return self._transition(invoice, InvoiceStatus.FAILED)

    def mark_cancelled(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)
        return self._transition(invoice, InvoiceStatus.CANCELLED)

    def update_total(self, invoice_id: int, new_total: Decimal):
        invoice = self.get_invoice(invoice_id)
        if invoice.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED):
            raise ConflictError(
                f"Cannot update total on a {invoice.status.value} invoice"
            )
        invoice.total = new_total
        self.repo.save(invoice)
        self._commit_and_refresh(invoice)
        return invoice

    def delete_invoice(self, invoice_id: int):
        invoice = self.get_invoice(invoice_id)

        if invoice.status == InvoiceStatus.PAID:
            raise ConflictError("Cannot delete a paid invoice")

        self.repo.delete(invoice)
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise
