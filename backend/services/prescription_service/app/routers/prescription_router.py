from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.prescription_db import get_db
from app.schemas.prescription_schema import PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse
from app.services.prescription_service import PrescriptionService

router = APIRouter(prefix="/prescription", tags=["Prescription"])


def get_prescription_service(db: Session = Depends(get_db)) -> PrescriptionService:
    return PrescriptionService(db)


@router.get("", response_model=list[PrescriptionResponse])
def list_prescriptions(service: PrescriptionService = Depends(get_prescription_service)):
    return service.list_prescriptions()


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription(
    prescription_id: int,
    service: PrescriptionService = Depends(get_prescription_service),
):
    return service.get_prescription(prescription_id)


@router.post("", response_model=PrescriptionResponse, status_code=201)
def assign_prescription(
    prescription_data: PrescriptionCreate,
    service: PrescriptionService = Depends(get_prescription_service),
):
    return service.assign_prescription(prescription_data)


@router.put("/{prescription_id}", response_model=PrescriptionResponse)
def update_prescription(
    prescription_id: int,
    update_data: PrescriptionUpdate,
    service: PrescriptionService = Depends(get_prescription_service),
):
    return service.update_prescription(prescription_id, update_data)


@router.delete("/{prescription_id}", status_code=204)
def delete_prescription(
    prescription_id: int,
    service: PrescriptionService = Depends(get_prescription_service),
):
    service.delete_prescription(prescription_id)
    return None