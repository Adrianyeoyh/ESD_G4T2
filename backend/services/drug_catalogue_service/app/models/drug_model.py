from sqlalchemy import Column, Integer, String, Float
from app.config.drug_db import Base 

class Drug(Base):
    __tablename__ = "drug"

    __table_args__ = {"schema": "drug_schema"}
    
    drug_id = Column("drugId", Integer, primary_key=True, autoincrement=True)
    drug_name = Column("drugName", String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)