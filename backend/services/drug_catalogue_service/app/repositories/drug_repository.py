from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.drug_model import Drug

class DrugRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, drug_id: int) -> Drug | None:
        return self.db.query(Drug).filter(Drug.drug_id == drug_id).first()

    def get_by_name(self, drug_name: str) -> Drug | None:
        """Get a drug by its name (case-insensitive)"""
        return self.db.query(Drug).filter(
            func.lower(Drug.drug_name) == func.lower(drug_name)
        ).first()

    def list_all(self) -> list[Drug]:
        return self.db.query(Drug).all()

    def create(self, drug_name: str, quantity: int, price: Decimal) -> Drug:
        new_drug = Drug(drug_name=drug_name, quantity=quantity, price=price)
        self.db.add(new_drug)
        return new_drug
    
    def delete(self, drug: Drug) -> None:
        self.db.delete(drug)