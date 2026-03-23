from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.repositories.drug_repository import DrugRepository
from app.schemas.drug_schema import DrugCreate
from fastapi import HTTPException
from utils.exceptions import ValidationError, ConflictError

class DrugService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DrugRepository(db)

    def list_drugs(self):
        try:
            return self.repo.list_all()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve drugs from catalogue"
            )

    def get_drug(self, drug_id: int):
        if not isinstance(drug_id, int) or drug_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="Drug ID must be a positive integer"
            )
        
        drug = self.repo.get_by_id(drug_id)
        if not drug:
            raise HTTPException(
                status_code=404,
                detail=f"Drug with ID {drug_id} not found in catalogue"
            )
        return drug

    def add_drug(self, drug_data: DrugCreate):
        try:
            # Check for duplicate drug name (case-insensitive)
            existing_drug = self.repo.get_by_name(drug_data.drug_name)
            if existing_drug:
                raise HTTPException(
                    status_code=409,
                    detail=f"Drug with name '{drug_data.drug_name}' already exists in catalogue"
                )
            
            # Create the drug
            drug = self.repo.create(
                drug_data.drug_name,
                drug_data.quantity,
                drug_data.price
            )
            self.db.commit()
            self.db.refresh(drug)
            return drug
        except HTTPException:
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Failed to add drug: database constraint violation"
            )
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to add drug to catalogue"
            )

    def update_quantity(self, drug_id: int, new_quantity: int):
        try:
            if not isinstance(new_quantity, int) or new_quantity < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Quantity must be a non-negative integer"
                )
            
            drug = self.get_drug(drug_id)
            drug.quantity = new_quantity
            self.repo.save(drug)
            self.db.commit()
            self.db.refresh(drug)
            return drug
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to update drug quantity"
            )

    def delete_drug(self, drug_id: int):
        try:
            drug = self.get_drug(drug_id)
            self.repo.delete(drug)
            self.db.commit()
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to delete drug from catalogue"
            )