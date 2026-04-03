"""
Request/Response validation schemas for the prescribe medicine composite service
"""
from typing import Optional, List


class MedicinePrescriptionItem:
    """Schema for a single medicine prescription item"""
    def __init__(self, drug_id: int, quantity: int, dosage: str):
        self.drug_id = drug_id
        self.quantity = quantity
        self.dosage = dosage

    @staticmethod
    def validate(item: dict) -> None:
        """Validate prescription item"""
        required = ["drugId", "quantity", "dosage"]
        for field in required:
            if field not in item:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(item["drugId"], int) or item["drugId"] <= 0:
            raise ValueError("drugId must be a positive integer")

        if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
            raise ValueError("quantity must be a positive integer")

        if not isinstance(item["dosage"], str) or not item["dosage"].strip():
            raise ValueError("dosage must be a non-empty string")

        if len(item["dosage"]) > 255:
            raise ValueError("dosage exceeds maximum length (255 characters)")


class PrescribeMedicineRequest:
    """Schema for prescribe medicine request"""
    def __init__(self, items: List[dict]):
        self.items = items

    @staticmethod
    def validate(data: dict) -> None:
        """Validate request data"""
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object")

        if "items" not in data:
            raise ValueError("Missing required field: items")

        if not isinstance(data["items"], list):
            raise ValueError("items must be an array")

        if not data["items"]:
            raise ValueError("items array cannot be empty")

        for idx, item in enumerate(data["items"]):
            try:
                MedicinePrescriptionItem.validate(item)
            except ValueError as e:
                raise ValueError(f"items[{idx}]: {str(e)}")


class PrescribeMedicineResponse:
    """Schema for successful prescribe medicine response"""
    schema = {
        "type": "object",
        "properties": {
            "recordId": {
                "type": "integer",
                "description": "Clinical record ID"
            },
            "patientId": {
                "type": ["string", "null"],
                "description": "Patient ID from clinical record"
            },
            "items": {
                "type": "array",
                "description": "List of prescribed medicines",
                "items": {
                    "type": "object",
                    "properties": {
                        "drugId": {"type": "integer"},
                        "drugName": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "dosage": {"type": "string"},
                        "unitPrice": {"type": "string"},
                        "lineTotal": {"type": "string"},
                        "prescriptionId": {"type": "string"}
                    }
                }
            },
            "invoice": {
                "type": "object",
                "description": "Invoice details from invoice service"
            },
            "total": {
                "type": "string",
                "description": "Total amount as decimal string"
            },
            "status": {
                "type": "string",
                "enum": ["success"],
                "description": "Operation status"
            }
        },
        "required": ["recordId", "items", "invoice", "total", "status"]
    }


class ErrorResponse:
    """Schema for error responses"""
    schema = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Human-readable error message"
            },
            "error": {
                "type": "string",
                "description": "Error code"
            },
            "details": {
                "type": "object",
                "description": "Additional error details (optional)"
            }
        },
        "required": ["message", "error"]
    }


# Error codes reference
ERROR_CODES = {
    "VALIDATION_ERROR": {
        "status": 400,
        "description": "Request validation failed",
        "examples": [
            "Missing required field: items",
            "items[0].drugId must be a positive integer",
            "items array cannot be empty"
        ]
    },
    "NOT_FOUND": {
        "status": 404,
        "description": "Resource not found",
        "examples": [
            "Clinical record 1234 not found",
            "Drug with id 999 not found"
        ]
    },
    "CONFLICT": {
        "status": 409,
        "description": "Resource state conflict",
        "examples": [
            "Insufficient stock for drug 123. Available: 5, Requested: 10",
            "Cannot prescribe for closed clinical record 1234"
        ]
    },
    "APPLICATION_ERROR": {
        "status": 500,
        "description": "Application error",
        "examples": [
            "Failed to update drug stock",
            "Clinical record service unavailable"
        ]
    },
    "DOWNSTREAM_TIMEOUT": {
        "status": 503,
        "description": "Downstream service request timed out"
    },
    "DOWNSTREAM_CONNECTION_ERROR": {
        "status": 503,
        "description": "Unable to reach downstream service"
    },
    "INTERNAL_SERVER_ERROR": {
        "status": 500,
        "description": "Unexpected internal server error"
    }
}
