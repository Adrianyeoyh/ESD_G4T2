from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


# ✅ CREATE
class RecordCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    patient_id: int
    visit_notes: str | None = None

    @field_validator("patient_id")
    @classmethod
    def validate_patient_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Patient ID must be greater than 0")
        return v

    @field_validator("visit_notes")
    @classmethod
    def validate_visit_notes(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError("Visit notes cannot be empty if provided")
            if len(v) > 255:
                raise ValueError("Visit notes cannot exceed 255 characters")
        return v


# ✅ UPDATE
class RecordUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    visit_notes: str | None = None
    is_closed: bool | None = None

    @field_validator("visit_notes")
    @classmethod
    def validate_visit_notes(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError("Visit notes cannot be empty if provided")
            if len(v) > 255:
                raise ValueError("Visit notes cannot exceed 255 characters")
        return v


# ✅ RESPONSE
class RecordResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    record_id: int
    patient_id: int
    date: datetime
    visit_notes: str | None
    is_closed: bool