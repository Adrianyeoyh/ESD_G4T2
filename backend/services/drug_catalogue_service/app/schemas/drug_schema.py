from pydantic import AliasChoices, BaseModel, ConfigDict, Field

class DrugCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    drug_name: str = Field(validation_alias=AliasChoices("drug_name", "drugName"))
    quantity: int
    price: float

class DrugUpdateQuantity(BaseModel):
    quantity: int

class DrugResponse(BaseModel):
    drug_id: int
    drug_name: str
    quantity: int
    price: float

    class Config:
        from_attributes = True