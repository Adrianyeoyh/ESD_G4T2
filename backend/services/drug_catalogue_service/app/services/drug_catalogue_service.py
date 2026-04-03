from sqlalchemy.orm import Session
from app.repositories.drug_catalogue_repository import DrugRepository
from app.schemas.drug_catalogue_schema import DrugCreate, DrugUpdate
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
            drug_data.price
        )
        self.db.commit()
        self.db.refresh(drug)
        return drug

    def update_drug(self, drug_id: int, update_data: DrugUpdate):
        drug = self.get_drug(drug_id)

        if update_data.drug_name != drug.drug_name:
            existing = self.repo.get_by_name(update_data.drug_name)
            if existing and existing.drug_id != drug_id:
                raise ConflictError(
                    f"Drug with name '{update_data.drug_name}' already exists in catalogue"
                )

        drug.drug_name = update_data.drug_name
        drug.quantity = update_data.quantity
        drug.price = update_data.price
        self.db.commit()
        self.db.refresh(drug)
        return drug

    def update_quantity(self, drug_id: int, new_quantity: int):
        if new_quantity < 0:
            raise ValidationError("Quantity must be a non-negative integer")

        drug = self.get_drug(drug_id)
        drug.quantity = new_quantity
        self.db.commit()
        self.db.refresh(drug)
        return drug

    def deduct_quantity(self, drug_id: int, amount: int):
        """Atomically deduct stock. Raises ConflictError if insufficient."""
        if amount <= 0:
            raise ValidationError("Deduction amount must be positive")

        drug = self.get_drug(drug_id)
        if drug.quantity < amount:
            raise ConflictError(
                f"Insufficient stock for drug {drug_id}. "
                f"Available: {drug.quantity}, Requested: {amount}"
            )
        drug.quantity -= amount
        self.db.commit()
        self.db.refresh(drug)
        return drug

    def restore_quantity(self, drug_id: int, amount: int):
        """Atomically restore stock (for rollback scenarios)."""
        if amount <= 0:
            raise ValidationError("Restore amount must be positive")

        drug = self.get_drug(drug_id)
        drug.quantity += amount
        self.db.commit()
        self.db.refresh(drug)
        return drug

    def delete_drug(self, drug_id: int):
        drug = self.get_drug(drug_id)
        self.repo.delete(drug)
        self.db.commit()