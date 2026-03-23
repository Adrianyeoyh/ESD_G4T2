from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, CheckConstraint, Index, func
from app.config.drug_db import Base 

class Drug(Base):
    __tablename__ = "drug"

    __table_args__ = (
        UniqueConstraint("drugName", name="uq_drug_name"),
        CheckConstraint("quantity >= 0", name="ck_quantity_non_negative"),
        CheckConstraint("price > 0", name="ck_price_positive"),
        Index("ix_drug_name_lower", func.lower("drugName"), name="ix_drug_name_ci"),
        {"schema": "drug_schema"}
    )
    
    drug_id = Column("drugId", Integer, primary_key=True, autoincrement=True)
    drug_name = Column("drugName", String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False)