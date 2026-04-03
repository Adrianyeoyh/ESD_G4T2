from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.repositories.prescription_repository import PrescriptionRepository
from app.schemas.prescription_schema import PrescriptionCreate, PrescriptionUpdate
from utils.exceptions import ValidationError, NotFoundError


class PrescriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PrescriptionRepository(db)

    def list_prescriptions(self) -> list:
        return self.repo.list_all()

    def get_prescription(self, prescription_id: int):
        if prescription_id <= 0:
            raise ValidationError("Prescription ID must be a positive integer")

        prescription = self.repo.get_by_id(prescription_id)
        if not prescription:
            raise NotFoundError(f"Prescription with ID {prescription_id} not found")
        return prescription

    def get_prescriptions_by_record(self, record_id: int) -> list:
        """Get all prescriptions for a record."""
        if record_id <= 0:
            raise ValidationError("Record ID must be a positive integer")
        return self.repo.get_by_record_id(record_id)

    def create_prescription(self, prescription_data: PrescriptionCreate) -> dict:
        """Create a prescription with multiple drugs."""
        # Create all prescription items in batch
        prescriptions = self.repo.create_batch(
            record_id=prescription_data.record_id,
            drugs=[{
                "drug_id": drug.drug_id,
                "drug_name": drug.drug_name,
                "quantity": drug.quantity,
            } for drug in prescription_data.drugs]
        )

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ValidationError("Invalid prescription data")

        # Refresh all prescriptions to get IDs
        for p in prescriptions:
            self.db.refresh(p)

        # Return grouped response
        # Use the first prescription_id as the "group" ID
        first_id = prescriptions[0].prescription_id if prescriptions else None

        return {
            "prescriptionId": first_id,
            "recordId": prescription_data.record_id,
            "drugs": [{
                "prescriptionId": p.prescription_id,
                "drugId": p.drug_id,
                "drugName": p.drug_name,
                "quantity": p.quantity,
            } for p in prescriptions]
        }

    def update_prescription(self, prescription_id: int, update_data: PrescriptionUpdate):
        prescription = self.get_prescription(prescription_id)

        if update_data.quantity is None:
            raise ValidationError("quantity must be provided for update")

        self.repo.update(prescription, quantity=update_data.quantity)

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ValidationError("Invalid update data")

        self.db.refresh(prescription)
        return prescription

    def delete_prescription(self, prescription_id: int):
        prescription = self.get_prescription(prescription_id)
        self.repo.delete(prescription)
        self.db.commit()

    def delete_prescriptions_by_record(self, record_id: int) -> int:
        """Delete all prescriptions for a record."""
        if record_id <= 0:
            raise ValidationError("Record ID must be a positive integer")
        count = self.repo.delete_by_record_id(record_id)
        self.db.commit()
        return count
