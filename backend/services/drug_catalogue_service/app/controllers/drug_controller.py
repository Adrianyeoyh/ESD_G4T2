from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.drug_db import get_db
from app.schemas.drug_schema import DrugCreate, DrugUpdateQuantity, DrugResponse
from app.services.drug_service import DrugService

router = APIRouter(prefix="/drug", tags=["Drug Catalogue"])

# inject the database session
@router.post("", response_model=DrugResponse, status_code=201)
def create_drug(drug_data: DrugCreate, db: Session = Depends(get_db)):
    service = DrugService(db)
    return service.add_drug(drug_data)

@router.get("", response_model=list[DrugResponse])
def get_all_drugs(db: Session = Depends(get_db)):
    service = DrugService(db)
    return service.repo.list_all()

@router.put("/{drug_id}", response_model=DrugResponse)
def update_drug(drug_id: int, update_data: DrugUpdateQuantity, db: Session = Depends(get_db)):
    service = DrugService(db)
    return service.update_quantity(drug_id, update_data.quantity)

@router.delete("/{drug_id}", status_code=204)
def delete_drug(drug_id: int, db: Session = Depends(get_db)):
    service = DrugService(db)
    service.delete_drug(drug_id)
    return