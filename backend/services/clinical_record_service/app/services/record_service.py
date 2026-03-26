from sqlalchemy.orm import Session

from app.repositories.record_repository import RecordRepository
from app.schemas.record_schema import (
    RecordCreate,
    RecordUpdate,
)
from utils.exceptions import ConflictError, NotFoundError, ValidationError


class RecordService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RecordRepository(db)

    # ✅ LIST all records
    def list_records(self):
        return self.repo.list_all()

    # ✅ GET record by ID (matches GET /record/{recordId})
    def get_record_by_id(self, record_id: int):
        if record_id <= 0:
            raise ValidationError("Clinical Record ID must be a positive integer")

        record = self.repo.get_by_id(record_id)
        if not record:
            raise NotFoundError(f"Clinical Record with ID {record_id} not found")

        return record

    # ✅ CREATE record
    def create_record(self, record_data: RecordCreate):
        record = self.repo.create(
            patient_id=record_data.patient_id,
            visit_notes=record_data.visit_notes,
        )

        self.db.commit()
        self.db.refresh(record)
        return record

    # ✅ UPDATE record
    def update_record(self, record_id: int, update_data: RecordUpdate):
        record = self.get_record_by_id(record_id)

        # Update only if values provided
        if update_data.visit_notes is not None:
            record.visit_notes = update_data.visit_notes

        if update_data.is_closed is not None:
            record.is_closed = update_data.is_closed

        self.repo.save(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    # ✅ DELETE record
    def delete_record(self, record_id: int):
        record = self.get_record_by_id(record_id)
        self.repo.delete(record)
        self.db.commit()