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

    def assign_prescription(self, prescription_data: PrescriptionCreate):
        if prescription_data.quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")

        if prescription_data.drug_id <= 0:
            raise ValidationError("drugId must be a positive integer")

        if prescription_data.record_id is not None and prescription_data.record_id <= 0:
            raise ValidationError("recordId must be a positive integer when provided")

        assigned_record_id = prescription_data.record_id if prescription_data.record_id is not None else self.repo.get_next_record_id()

        prescription = self.repo.create(
            assigned_record_id,
            prescription_data.drug_id,
            prescription_data.quantity,
            prescription_data.dosage,
        )
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ValidationError("Invalid prescription data. Check quantity and dosage values.")

        self.db.refresh(prescription)
        return prescription

    def update_prescription(self, prescription_id: int, update_data: PrescriptionUpdate):
        prescription = self.get_prescription(prescription_id)

        if not update_data.quantity and not update_data.dosage:
            raise ValidationError("At least one field (quantity or dosage) must be provided for update")

        self.repo.update(
            prescription,
            quantity=update_data.quantity,
            dosage=update_data.dosage,
        )
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ValidationError("Invalid update data. Check quantity and dosage values.")

        self.db.refresh(prescription)
        return prescription

    def delete_prescription(self, prescription_id: int):
        prescription = self.get_prescription(prescription_id)
        self.repo.delete(prescription)
        self.db.commit()