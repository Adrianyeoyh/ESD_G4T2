from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.drug_db import get_db
from app.controllers.drug_controller import DrugController
from app.schemas.drug_schema import DrugCreate, DrugUpdateQuantity, DrugResponse

router = APIRouter(prefix="/drug", tags=["Drug Catalogue"])
controller = DrugController()


@router.post("", response_model=DrugResponse, status_code=201)
def create_drug(drug_data: DrugCreate, db: Session = Depends(get_db)):
    return controller.create_drug(drug_data, db)


@router.get("", response_model=list[DrugResponse])
def get_all_drugs(db: Session = Depends(get_db)):
    return controller.get_all_drugs(db)


@router.put("/{drug_id}", response_model=DrugResponse)
def update_drug(drug_id: int, update_data: DrugUpdateQuantity, db: Session = Depends(get_db)):
    return controller.update_drug(drug_id, update_data, db)


@router.delete("/{drug_id}", status_code=204)
def delete_drug(drug_id: int, db: Session = Depends(get_db)):
    controller.delete_drug(drug_id, db)
    return None