from sqlalchemy.orm import Session
from app.models.drug_model import Drug

class DrugRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, drug_id: int) -> Drug | None:
        return self.db.query(Drug).filter(Drug.drugId == drug_id).first()

    def list_all(self) -> list[Drug]:
        return self.db.query(Drug).all()

    def create(self, drugName: str, quantity: int, price: float) -> Drug:
        new_drug = Drug(drugName=drugName, quantity=quantity, price=price)
        self.db.add(new_drug)
        return new_drug
    
    def save(self, drug: Drug) -> Drug:
        self.db.add(drug)
        return drug
        
    def delete(self, drug: Drug) -> None:
        self.db.delete(drug)