from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.prescription_db import get_db
from app.schemas.prescription_schema import PrescriptionCreate, PrescriptionResponse
from app.services.prescription_service import PrescriptionService

router = APIRouter(prefix="/prescription", tags=["Prescription"])


def get_prescription_service(db: Session = Depends(get_db)) -> PrescriptionService:
    return PrescriptionService(db)


@router.post("", response_model=PrescriptionResponse, status_code=201)
def assign_prescription(
    prescription_data: PrescriptionCreate,
    service: PrescriptionService = Depends(get_prescription_service),
):
    return service.assign_prescription(prescription_data)