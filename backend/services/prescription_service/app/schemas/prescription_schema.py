from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

class PrescriptionCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    record_id: Optional[int] = None
    drug_id: int
    quantity: int
    dosage: str = Field(min_length=1, max_length=255)

    @field_validator("record_id", "drug_id")
    @classmethod
    def validate_positive_ids(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("ID values must be positive integers")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("dosage")
    @classmethod
    def validate_dosage(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Dosage cannot be empty or contain only whitespace")
        return v.strip()


class PrescriptionResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
    prescription_id: int
    record_id: int
    drug_id: int
    quantity: int
    dosage: str