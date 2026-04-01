from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class DrugCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    drug_name: str = Field(min_length=1)
    quantity: int
    price: Decimal
    purpose: str | None = None
    recommended_dosage: str | None = None
    remarks: str | None = None

    @field_validator("drug_name")
    @classmethod
    def validate_drug_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Drug name cannot be empty or contain only whitespace")
        if len(v) > 255:
            raise ValueError("Drug name cannot exceed 255 characters")
        return v.strip()

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        if v > Decimal("999999.99"):
            raise ValueError("Price cannot exceed 999999.99")
        return v

    @field_validator("purpose", "recommended_dosage", "remarks")
    @classmethod
    def normalize_optional_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        normalized = v.strip()
        return normalized or None


class DrugUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    quantity: int | None = None
    price: Decimal | None = None
    purpose: str | None = None
    recommended_dosage: str | None = None
    remarks: str | None = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        if v > Decimal("999999.99"):
            raise ValueError("Price cannot exceed 999999.99")
        return v

    @field_validator("purpose", "recommended_dosage", "remarks")
    @classmethod
    def validate_optional_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        normalized = v.strip()
        return normalized or None


class DrugResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    drug_id: int
    drug_name: str
    quantity: int
    price: Decimal
    purpose: str | None = None
    recommended_dosage: str | None = None
    remarks: str | None = None
