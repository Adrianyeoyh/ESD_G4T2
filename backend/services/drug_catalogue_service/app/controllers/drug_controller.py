from sqlalchemy.orm import Session
from app.schemas.drug_schema import DrugCreate, DrugUpdateQuantity, DrugResponse
from app.services.drug_service import DrugService

class DrugController:
    def create_drug(self, drug_data: DrugCreate, db: Session) -> DrugResponse:
        service = DrugService(db)
        return service.add_drug(drug_data)

    def get_all_drugs(self, db: Session) -> list[DrugResponse]:
        service = DrugService(db)
        return service.list_drugs()

    def update_drug(self, drug_id: int, update_data: DrugUpdateQuantity, db: Session) -> DrugResponse:
        service = DrugService(db)
        return service.update_quantity(drug_id, update_data.quantity)

    def delete_drug(self, drug_id: int, db: Session) -> None:
        service = DrugService(db)
        service.delete_drug(drug_id)