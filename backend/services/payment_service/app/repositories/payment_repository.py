from app.models.payment_model import Payment


class PaymentRepository:
    def __init__(self, db):
        self.db = db

    def create(
        self,
        invoice_id: int,
        record_id: int,
        payment_intent_id: str,
        client_secret: str,
        attempt_number: int,
        amount: float,
        currency: str,
        provider: str = "stripe",
    ) -> Payment:
        payment = Payment(
            invoice_id=invoice_id,
            record_id=record_id,
            payment_intent_id=payment_intent_id,
            client_secret=client_secret,
            attempt_number=attempt_number,
            amount=amount,
            currency=currency,
            provider=provider,
        )
        self.db.add(payment)
        return payment

    def get_by_id(self, payment_id: int) -> Payment | None:
        return (
            self.db.query(Payment)
            .filter(Payment.payment_id == payment_id)
            .first()
        )

    def get_by_payment_intent_id(self, payment_intent_id: str) -> Payment | None:
        return (
            self.db.query(Payment)
            .filter(Payment.payment_intent_id == payment_intent_id)
            .first()
        )

    def get_latest_by_invoice_id(self, invoice_id: int) -> Payment | None:
        return (
            self.db.query(Payment)
            .filter(Payment.invoice_id == invoice_id)
            .order_by(Payment.created_at.desc())
            .first()
        )

    def list_by_invoice_id(self, invoice_id: int) -> list[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.invoice_id == invoice_id)
            .order_by(Payment.created_at.desc())
            .all()
        )

    def count_by_invoice_id(self, invoice_id: int) -> int:
        return (
            self.db.query(Payment)
            .filter(Payment.invoice_id == invoice_id)
            .count()
        )

    def save(self, payment: Payment) -> Payment:
        self.db.add(payment)
        return payment