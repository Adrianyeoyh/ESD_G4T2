from sqlalchemy.exc import SQLAlchemyError
from app.config.db import SessionLocal
from app.repositories.invoice_repository import InvoiceRepository
from utils.exceptions import NotFoundError, ConflictError, AppError
from common.tools import InvoiceStatus


class InvoiceService:
    def create_invoice(self, record_id: int, total: float):
        db = SessionLocal()
        try:
            repo = InvoiceRepository(db)

            existing = repo.get_by_record_id(record_id)
            if existing:
                raise ConflictError("Invoice already exists for this record")

            invoice = repo.create(record_id, total)
            db.commit()
            db.refresh(invoice)
            return invoice

        except AppError:
            db.rollback()
            raise
        except SQLAlchemyError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_invoice(self, invoice_id: int):
        db = SessionLocal()
        try:
            repo = InvoiceRepository(db)
            invoice = repo.get_by_id(invoice_id)

            if not invoice:
                raise NotFoundError("Invoice not found")

            return invoice
        finally:
            db.close()

    def get_invoice_by_record_id(self, record_id: int):
        db = SessionLocal()
        try:
            repo = InvoiceRepository(db)
            invoice = repo.get_by_record_id(record_id)

            if not invoice:
                raise NotFoundError("Invoice not found for this record")

            return invoice
        finally:
            db.close()

    def list_invoices(self):
        db = SessionLocal()
        try:
            repo = InvoiceRepository(db)
            return repo.list_all()
        finally:
            db.close()

    def mark_payment_pending(self, invoice_id: int):
        db = SessionLocal()
        try:
            repo = InvoiceRepository(db)
            invoice = repo.get_by_id(invoice_id)

            if not invoice:
                raise NotFoundError("Invoice not found")

            if invoice.status == InvoiceStatus.PAID:
                raise ConflictError("Invoice is already paid")

            invoice.status = InvoiceStatus.PAYMENT_PENDING
            repo.save(invoice)

            db.commit()
            db.refresh(invoice)
            return invoice

        except AppError:
            db.rollback()
            raise
        except SQLAlchemyError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def mark_paid(self, invoice_id: int):
        db = SessionLocal()
        try:
            repo = InvoiceRepository(db)
            invoice = repo.get_by_id(invoice_id)

            if not invoice:
                raise NotFoundError("Invoice not found")

            if invoice.status == InvoiceStatus.PAID:
                raise ConflictError("Invoice is already paid")

            invoice.status = InvoiceStatus.PAID
            repo.save(invoice)

            db.commit()
            db.refresh(invoice)
            return invoice

        except AppError:
            db.rollback()
            raise
        except SQLAlchemyError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def mark_failed(self, invoice_id: int):
        db = SessionLocal()
        try:
            repo = InvoiceRepository(db)
            invoice = repo.get_by_id(invoice_id)

            if not invoice:
                raise NotFoundError("Invoice not found")

            if invoice.status == InvoiceStatus.PAID:
                raise ConflictError("Cannot mark a paid invoice as failed")

            invoice.status = InvoiceStatus.FAILED
            repo.save(invoice)

            db.commit()
            db.refresh(invoice)
            return invoice

        except AppError:
            db.rollback()
            raise
        except SQLAlchemyError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def mark_cancelled(self, invoice_id: int):
        db = SessionLocal()
        try:
            repo = InvoiceRepository(db)
            invoice = repo.get_by_id(invoice_id)

            if not invoice:
                raise NotFoundError("Invoice not found")

            if invoice.status == InvoiceStatus.PAID:
                raise ConflictError("Cannot cancel a paid invoice")

            invoice.status = InvoiceStatus.CANCELLED
            repo.save(invoice)

            db.commit()
            db.refresh(invoice)
            return invoice

        except AppError:
            db.rollback()
            raise
        except SQLAlchemyError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()