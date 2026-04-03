from sqlalchemy.orm import Session
from app.repositories.drug_repository import DrugRepository
from app.schemas.drug_schema import DrugCreate
from utils.exceptions import ConflictError, NotFoundError, ValidationError

class DrugService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DrugRepository(db)

    def list_drugs(self):
        return self.repo.list_all()

    def get_drug(self, drug_id: int):
        if drug_id <= 0:
            raise ValidationError("Drug ID must be a positive integer")
        
        drug = self.repo.get_by_id(drug_id)
        if not drug:
            raise NotFoundError(f"Drug with ID {drug_id} not found in catalogue")
        return drug

    def add_drug(self, drug_data: DrugCreate):
        # Check for duplicate drug name (case-insensitive)
        existing_drug = self.repo.get_by_name(drug_data.drug_name)
        if existing_drug:
            raise ConflictError(
                f"Drug with name '{drug_data.drug_name}' already exists in catalogue"
            )

        drug = self.repo.create(
            drug_data.drug_name,
            drug_data.quantity,
            drug_data.price,
            drug_data.purpose,
            drug_data.recommended_dosage,
            drug_data.remarks,
        )
        self.db.commit()
        self.db.refresh(drug)
        return drug

    def update_drug(
        self,
        drug_id: int,
        quantity: int | None,
        price,
        purpose: str | None,
        recommended_dosage: str | None,
        remarks: str | None,
        provided_fields: set[str] | None = None,
    ):
        provided_fields = provided_fields or set()
        if (
            "quantity" not in provided_fields
            and "price" not in provided_fields
            and "purpose" not in provided_fields
            and "recommended_dosage" not in provided_fields
            and "remarks" not in provided_fields
        ):
            raise ValidationError(
                "At least one field (quantity, price, purpose, recommendedDosage, remarks) must be provided"
            )

        if "quantity" in provided_fields and quantity is None:
            raise ValidationError("Quantity cannot be null")
        if quantity is not None and quantity < 0:
            raise ValidationError("Quantity must be a non-negative integer")

        if "price" in provided_fields and price is None:
            raise ValidationError("Price cannot be null")
        if price is not None and price <= 0:
            raise ValidationError("Price must be greater than 0")

        drug = self.get_drug(drug_id)
        if "quantity" in provided_fields:
            drug.quantity = quantity
        if "price" in provided_fields:
            drug.price = price
        if "purpose" in provided_fields:
            drug.purpose = purpose
        if "recommended_dosage" in provided_fields:
            drug.recommended_dosage = recommended_dosage
        if "remarks" in provided_fields:
            drug.remarks = remarks
        self.repo.save(drug)
        self.db.commit()
        self.db.refresh(drug)
        return drug

    def delete_drug(self, drug_id: int):
        drug = self.get_drug(drug_id)
        self.repo.delete(drug)
        self.db.commit()
