from sqlalchemy import CheckConstraint, Column, Index, Integer, Numeric, String, UniqueConstraint, func

from app.config.drug_db import Base
from app.config.settings import DB_SCHEMA

class Drug(Base):
    __tablename__ = "drug"

    drug_id = Column("drugId", Integer, primary_key=True, autoincrement=True)
    drug_name = Column("drugName", String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("drugName", name="uq_drug_name"),
        CheckConstraint("quantity >= 0", name="ck_quantity_non_negative"),
        CheckConstraint("price > 0", name="ck_price_positive"),
        Index("ix_drug_name_ci", func.lower(drug_name)),
        {"schema": DB_SCHEMA},
    )
