from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.prescription_model import Prescription

class PrescriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, prescription_id: int) -> Prescription | None:
        return self.db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()

    def list_all(self) -> list[Prescription]:
        return self.db.query(Prescription).all()

    def create(self, record_id: int, drug_id: int, quantity: int, dosage: str) -> Prescription:
        prescription = Prescription(
            record_id=record_id,
            drug_id=drug_id,
            quantity=quantity,
            dosage=dosage,
        )
        self.db.add(prescription)
        return prescription

    def get_next_record_id(self) -> int:
        current_max = self.db.query(func.max(Prescription.record_id)).scalar()
        return (current_max or 0) + 1

    def update(self, prescription: Prescription, quantity: int | None = None, dosage: str | None = None) -> Prescription:
        if quantity is not None:
            prescription.quantity = quantity
        if dosage is not None:
            prescription.dosage = dosage
        self.db.add(prescription)
        return prescription

    def delete(self, prescription: Prescription) -> None:
        self.db.delete(prescription)
