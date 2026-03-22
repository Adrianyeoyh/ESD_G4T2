from pydantic import BaseModel

class DrugCreate(BaseModel):
    drugName: str
    quantity: int
    price: float

class DrugUpdateQuantity(BaseModel):
    quantity: int

class DrugResponse(BaseModel):
    drugId: int
    drugName: str
    quantity: int
    price: float

    class Config:
        from_attributes = True