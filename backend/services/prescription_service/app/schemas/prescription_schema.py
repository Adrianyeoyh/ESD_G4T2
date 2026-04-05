from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class DrugItem(BaseModel):
    """Schema for a single drug in a prescription."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    drug_id: int
    drug_name: str
    quantity: int

    @field_validator("drug_id")
    @classmethod
    def validate_drug_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("drugId must be a positive integer")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("drug_name")
    @classmethod
    def validate_drug_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("drugName cannot be empty")
        return v.strip()


class PrescriptionCreate(BaseModel):
    """Schema for creating a prescription with multiple drugs."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    record_id: int
    drugs: List[DrugItem]

    @field_validator("record_id")
    @classmethod
    def validate_record_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("recordId must be a positive integer")
        return v

    @field_validator("drugs")
    @classmethod
    def validate_drugs(cls, v: List[DrugItem]) -> List[DrugItem]:
        if not v:
            raise ValueError("drugs list cannot be empty")
        return v


class PrescriptionUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    quantity: Optional[int] = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class PrescriptionItemResponse(BaseModel):
    """Response for a single prescription item (drug)."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    prescription_id: int
    record_id: int
    drug_id: int
    drug_name: str
    quantity: int


class PrescriptionResponse(BaseModel):
    """Response for a prescription with all its drugs."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    prescription_id: int
    record_id: int
    drugs: List[dict]