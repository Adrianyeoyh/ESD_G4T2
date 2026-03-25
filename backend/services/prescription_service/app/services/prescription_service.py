from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.repositories.prescription_repository import PrescriptionRepository
from app.schemas.prescription_schema import PrescriptionCreate
from utils.exceptions import ValidationError

class PrescriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PrescriptionRepository(db)

    def assign_prescription(self, prescription_data: PrescriptionCreate):
        if prescription_data.quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")

        if prescription_data.drug_id <= 0:
            raise ValidationError("drugId must be a positive integer")

        if prescription_data.record_id is not None and prescription_data.record_id <= 0:
            raise ValidationError("recordId must be a positive integer when provided")

        prescription = self.repo.create(
            prescription_data.record_id,
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