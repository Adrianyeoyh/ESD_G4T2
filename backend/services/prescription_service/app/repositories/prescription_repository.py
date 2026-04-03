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

    def get_by_record_id(self, record_id: int) -> list[Prescription]:
        """Get all prescription items for a given record."""
        return self.db.query(Prescription).filter(Prescription.record_id == record_id).all()

    def create(self, record_id: int, drug_id: int, drug_name: str, quantity: int) -> Prescription:
        prescription = Prescription(
            record_id=record_id,
            drug_id=drug_id,
            drug_name=drug_name,
            quantity=quantity,
        )
        self.db.add(prescription)
        return prescription

    def create_batch(self, record_id: int, drugs: list[dict]) -> list[Prescription]:
        """Create multiple prescription items for a record."""
        prescriptions = []
        for drug in drugs:
            prescription = Prescription(
                record_id=record_id,
                drug_id=drug["drug_id"],
                drug_name=drug["drug_name"],
                quantity=drug["quantity"],
            )
            self.db.add(prescription)
            prescriptions.append(prescription)
        return prescriptions

    def update(self, prescription: Prescription, quantity: int | None = None) -> Prescription:
        if quantity is not None:
            prescription.quantity = quantity
        self.db.add(prescription)
        return prescription

    def delete(self, prescription: Prescription) -> None:
        self.db.delete(prescription)

    def delete_by_record_id(self, record_id: int) -> int:
        """Delete all prescriptions for a record. Returns count deleted."""
        count = self.db.query(Prescription).filter(Prescription.record_id == record_id).delete()
        return count
