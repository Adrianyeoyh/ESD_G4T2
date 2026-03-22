from sqlalchemy import Column, Integer, String, Float
from app.config.db import Base # Assuming your db.py is set up

class Drug(Base):
    __tablename__ = "drug"

    __table_args__ = {"schema": "drug_schema"}
    
    drugId = Column(Integer, primary_key=True, autoincrement=True)
    drugName = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)