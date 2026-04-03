from pydantic import field_serializer
from typing import Optional
from decimal import Decimal
from datetime import datetime

# Import standardized base schemas
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from common.schemas.base_schema import StrictCamelBaseModel, ORMCamelBaseModel


class InvoiceCreate(StrictCamelBaseModel):
    """
    Schema for creating invoices.
    
    ✅ Strict validation: extra fields (e.g., patientId, prescriptions) will be rejected.
    This prevents silent data loss from payload mismatches.
    """
    record_id: int
    total: Decimal


class InvoiceUpdateTotal(StrictCamelBaseModel):
    """Schema for updating invoice total."""
    total: Decimal


class InvoiceResponse(ORMCamelBaseModel):
    """
    Schema for invoice responses.
    
    Includes ORM compatibility (from_attributes=True) and strict validation.
    """
    invoice_id: int
    record_id: int
    total: Decimal
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer("status")
    def serialize_status(self, v) -> str:
        return v.value if hasattr(v, "value") else v

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        return v.isoformat() if v else None
