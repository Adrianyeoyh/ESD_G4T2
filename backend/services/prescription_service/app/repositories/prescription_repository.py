from sqlalchemy.orm import Session
from app.models.prescription_model import Prescription

class PrescriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, record_id: int, drug_id: int, quantity: int, dosage: str) -> Prescription:
        prescription = Prescription(
            record_id=record_id,
            drug_id=drug_id,
            quantity=quantity,
            dosage=dosage,
        )
        self.db.add(prescription)
        return prescription