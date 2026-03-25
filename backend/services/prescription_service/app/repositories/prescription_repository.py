from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.prescription_model import Prescription

class PrescriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_next_record_id(self) -> int:
        current_max = self.db.query(func.max(Prescription.record_id)).scalar()
        return (current_max or 0) + 1

    def create(self, record_id: int | None, drug_id: int, quantity: int, dosage: str) -> Prescription:
        assigned_record_id = record_id if record_id is not None else self.get_next_record_id()

        prescription = Prescription(
            record_id=assigned_record_id,
            drug_id=drug_id,
            quantity=quantity,
            dosage=dosage,
        )
        self.db.add(prescription)
        return prescription