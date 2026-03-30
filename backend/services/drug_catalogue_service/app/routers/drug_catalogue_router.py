from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.drug_catalogue_db import get_db
from app.schemas.drug_catalogue_schema import DrugCreate, DrugUpdate, DrugUpdateQuantity, DrugResponse
from app.services.drug_catalogue_service import DrugService

router = APIRouter(prefix="/drug", tags=["Drug Catalogue"])


def get_drug_service(db: Session = Depends(get_db)) -> DrugService:
    return DrugService(db)


@router.post("", response_model=DrugResponse, status_code=201)
def create_drug(drug_data: DrugCreate, service: DrugService = Depends(get_drug_service)):
    return service.add_drug(drug_data)


@router.get("", response_model=list[DrugResponse])
def get_all_drugs(service: DrugService = Depends(get_drug_service)):
    return service.list_drugs()


@router.get("/{drug_id}", response_model=DrugResponse)
def get_drug(drug_id: int, service: DrugService = Depends(get_drug_service)):
    return service.get_drug(drug_id)


@router.put("/{drug_id}", response_model=DrugResponse)
def update_drug(
    drug_id: int,
    update_data: DrugUpdate,
    service: DrugService = Depends(get_drug_service),
):
    return service.update_drug(drug_id, update_data)


@router.patch("/{drug_id}/quantity", response_model=DrugResponse)
def update_drug_quantity(
    drug_id: int,
    update_data: DrugUpdateQuantity,
    service: DrugService = Depends(get_drug_service),
):
    return service.update_quantity(drug_id, update_data.quantity)


@router.delete("/{drug_id}", status_code=204)
def delete_drug(drug_id: int, service: DrugService = Depends(get_drug_service)):
    service.delete_drug(drug_id)
    return None