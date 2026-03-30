from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.models.record_model import Record


class RecordRepository:
    def __init__(self, db: Session):
        self.db = db

    # GET /record/{recordId}
    def get_by_id(self, record_id: int) -> Record | None:
        return self.db.query(Record).filter(Record.record_id == record_id).first()

    # Optional: get all records for a patient
    def get_by_patient_id(self, patient_id: int) -> list[Record]:
        return self.db.query(Record).filter(
            Record.patient_id == patient_id
        ).all()

    # LIST all records
    def list_all(self) -> list[Record]:
        return self.db.query(Record).all()

    # CREATE record
    def create(
        self,
        patient_id: int,
        visit_notes: str | None = None,
        is_closed: bool = False,
        date: datetime | None = None,
    ) -> Record:
        new_record = Record(
            patient_id=patient_id,
            visit_notes=visit_notes,
            is_closed=is_closed,
            date=date or func.now(),
        )
        self.db.add(new_record)
        return new_record

    # UPDATE / SAVE
    def save(self, record: Record) -> Record:
        self.db.add(record)
        return record

    # DELETE
    def delete(self, record: Record) -> None:
        self.db.delete(record)