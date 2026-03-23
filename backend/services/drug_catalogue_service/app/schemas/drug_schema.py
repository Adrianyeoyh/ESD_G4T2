from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

class DrugCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    drug_name: str = Field(validation_alias=AliasChoices("drug_name", "drugName"), min_length=1)
    quantity: int
    price: float

    @field_validator('drug_name')
    @classmethod
    def validate_drug_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Drug name cannot be empty or contain only whitespace')
        if len(v) > 255:
            raise ValueError('Drug name cannot exceed 255 characters')
        return v.strip()

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        if v > 999999.99:
            raise ValueError('Price cannot exceed 999999.99')
        return v

class DrugUpdateQuantity(BaseModel):
    quantity: int

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v

class DrugResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    drug_id: int
    drug_name: str
    quantity: int
    price: float