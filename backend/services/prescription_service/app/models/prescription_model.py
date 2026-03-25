from sqlalchemy import CheckConstraint, Column, Integer, String

from app.config.prescription_db import Base
from app.config.settings import DB_SCHEMA

class Prescription(Base):
    __tablename__ = "prescription"

    prescription_id = Column("prescriptionId", Integer, primary_key=True, autoincrement=True)
    record_id = Column("recordId", Integer, nullable=False)
    drug_id = Column("drugId", Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    dosage = Column(String(255), nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_quantity_positive"),
        CheckConstraint('length(trim(dosage)) > 0', name="ck_dosage_not_blank"),
        {"schema": DB_SCHEMA},
    )
