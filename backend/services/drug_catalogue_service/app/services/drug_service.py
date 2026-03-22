from sqlalchemy.orm import Session
from app.repositories.drug_repository import DrugRepository
from app.schemas.drug_schema import DrugCreate
from fastapi import HTTPException

class DrugService:
    def __init__(self, db: Session):
        self.repo = DrugRepository(db)

    def get_drug(self, drug_id: int):
        drug = self.repo.get_by_id(drug_id)
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found in catalogue")
        return drug

    def add_drug(self, drug_data: DrugCreate):
        # Business logic: Maybe check if drug already exists before adding?
        # For now, just create it.
        drug = self.repo.create(drug_data.drugName, drug_data.quantity, drug_data.price)
        self.repo.db.commit()
        self.repo.db.refresh(drug)
        return drug

    def update_quantity(self, drug_id: int, new_quantity: int):
        drug = self.get_drug(drug_id) # Reuse the method above to check if it exists!
        drug.quantity = new_quantity
        self.repo.save(drug)
        self.repo.db.commit()
        self.repo.db.refresh(drug)
        return drug

    def delete_drug(self, drug_id: int):
        drug = self.get_drug(drug_id)
        self.repo.delete(drug)
        self.repo.db.commit()