from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from app.config.db import SessionLocal
from app.repositories.payment_repository import PaymentRepository
from app.services import stripe_service
from utils.exceptions import NotFoundError, ConflictError, AppError
from common.tools import PaymentStatus


class PaymentService:

    def create_payment_attempt(
        self,
        invoice_id: int,
        record_id: int,
        amount: float,
        currency: str,
        description: str | None = None,
    ):
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)

            attempt_number = repo.count_by_invoice_id(invoice_id) + 1

            if description is None:
                description = f"Invoice #{invoice_id} payment"

            intent = stripe_service.create_payment_intent(amount, currency, description)

            payment = repo.create(
                invoice_id=invoice_id,
                record_id=record_id,
                payment_intent_id=intent.id,
                client_secret=intent.client_secret,
                attempt_number=attempt_number,
                amount=amount,
                currency=currency,
            )

            db.commit()
            db.refresh(payment)
            return payment

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

    def get_payment(self, payment_id: int):
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            payment = repo.get_by_id(payment_id)

            if not payment:
                raise NotFoundError("Payment not found")

            return payment
        finally:
            db.close()

    def get_latest_payment_by_invoice_id(self, invoice_id: int):
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            payment = repo.get_latest_by_invoice_id(invoice_id)

            if not payment:
                raise NotFoundError("No payment found for this invoice")

            return payment
        finally:
            db.close()

    def list_payments_by_invoice_id(self, invoice_id: int):
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            return repo.list_by_invoice_id(invoice_id)
        finally:
            db.close()

    def mark_succeeded(self, payment_intent_id: str, paid_at: datetime | None = None):
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            payment = repo.get_by_payment_intent_id(payment_intent_id)

            if not payment:
                raise NotFoundError("Payment not found for this PaymentIntent")

            payment.status = PaymentStatus.SUCCEEDED
            payment.paid_at = paid_at or datetime.now(timezone.utc)
            repo.save(payment)

            db.commit()
            db.refresh(payment)
            return payment

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

    def mark_failed(
        self,
        payment_intent_id: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ):
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            payment = repo.get_by_payment_intent_id(payment_intent_id)

            if not payment:
                raise NotFoundError("Payment not found for this PaymentIntent")

            payment.status = PaymentStatus.FAILED
            payment.error_code = error_code
            payment.error_message = error_message
            repo.save(payment)

            db.commit()
            db.refresh(payment)
            return payment

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

    def mark_cancelled(self, payment_id: int):
        db = SessionLocal()
        try:
            repo = PaymentRepository(db)
            payment = repo.get_by_id(payment_id)

            if not payment:
                raise NotFoundError("Payment not found")

            if payment.status == PaymentStatus.SUCCEEDED:
                raise ConflictError("Cannot cancel a succeeded payment")

            stripe_service.cancel_payment_intent(payment.payment_intent_id)

            payment.status = PaymentStatus.CANCELLED
            payment.cancelled_at = datetime.now(timezone.utc)
            repo.save(payment)

            db.commit()
            db.refresh(payment)
            return payment

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