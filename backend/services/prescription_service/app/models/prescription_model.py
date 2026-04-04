from sqlalchemy import Column, Integer, String

from app.config.prescription_db import Base
from app.config.settings import DB_SCHEMA


class Prescription(Base):
    __tablename__ = "prescription"

    prescription_id = Column("prescriptionId", Integer, primary_key=True, autoincrement=True)
    record_id = Column("recordId", Integer, nullable=False)
    drug_id = Column("drugId", Integer, nullable=False)
    drug_name = Column("drugName", String(255), nullable=False)
    quantity = Column(Integer, nullable=False)

    __table_args__ = (
        {"schema": DB_SCHEMA},
    )
