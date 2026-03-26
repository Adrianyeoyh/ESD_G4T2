from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.record_db import get_db
from app.schemas.record_schema import (
    RecordCreate,
    RecordUpdate,
    RecordResponse,
)
from app.services.record_service import RecordService

router = APIRouter(prefix="/record", tags=["Clinical Records"])


def get_record_service(db: Session = Depends(get_db)) -> RecordService:
    return RecordService(db)


# ✅ CREATE record
@router.post("", response_model=RecordResponse, status_code=201)
def create_record(
    record_data: RecordCreate,
    service: RecordService = Depends(get_record_service),
):
    return service.create_record(record_data)


# ✅ GET ALL records
@router.get("", response_model=list[RecordResponse])
def get_all_records(service: RecordService = Depends(get_record_service)):
    return service.list_records()


# ✅ GET specific record (THIS matches your diagram)
@router.get("/{recordId}", response_model=RecordResponse)
def get_record(
    recordId: int,
    service: RecordService = Depends(get_record_service),
):
    return service.get_record_by_id(recordId)


# ✅ UPDATE record
@router.put("/{recordId}", response_model=RecordResponse)
def update_record(
    recordId: int,
    update_data: RecordUpdate,
    service: RecordService = Depends(get_record_service),
):
    return service.update_record(recordId, update_data)


# ✅ DELETE record
@router.delete("/{recordId}", status_code=204)
def delete_record(
    recordId: int,
    service: RecordService = Depends(get_record_service),
):
    service.delete_record(recordId)
    return None