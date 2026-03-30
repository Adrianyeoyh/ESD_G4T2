from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, CheckConstraint
from sqlalchemy.sql import func

from app.config.record_db import Base
from app.config.settings import DB_SCHEMA


class Record(Base):
    __tablename__ = "record"

    record_id = Column("recordId", Integer, primary_key=True, autoincrement=True)
    patient_id = Column("patientId", Integer, nullable=False)
    date = Column(DateTime, nullable=False, default=func.now())
    visit_notes = Column("visitNotes", String(255), nullable=True)
    is_closed = Column("isClosed", Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint('"patientId" > 0', name="ck_patient_id_positive"),
        Index("ix_record_patient_id", "patientId"),
        {"schema": DB_SCHEMA},
    )