"""
Request/Response validation schemas for the prescribe medicine composite service
"""
from typing import List


class MedicinePrescriptionItem:
    """Schema for a single medicine prescription item"""
    def __init__(self, drug_name: str, quantity: int):
        self.drug_name = drug_name
        self.quantity = quantity

    @staticmethod
    def validate(item: dict) -> None:
        """Validate prescription item"""
        required = ["drugName", "quantity"]
        for field in required:
            if field not in item:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(item["drugName"], str) or not item["drugName"].strip():
            raise ValueError("drugName must be a non-empty string")

        if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
            raise ValueError("quantity must be a positive integer")


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
            "drugs": {
                "type": "array",
                "description": "List of prescribed drugs",
                "items": {
                    "type": "object",
                    "properties": {
                        "drugId": {"type": "integer"},
                        "drugName": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "unitPrice": {"type": "string"},
                        "lineTotal": {"type": "string"},
                        "prescriptionId": {"type": "integer"}
                    }
                }
            },
            "totalPrice": {
                "type": "string",
                "description": "Total price as decimal string"
            },
            "status": {
                "type": "string",
                "enum": ["success"],
                "description": "Operation status"
            }
        },
        "required": ["recordId", "drugs", "totalPrice", "status"]
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
            "items[0].drugName must be a non-empty string",
            "items array cannot be empty"
        ]
    },
    "NOT_FOUND": {
        "status": 404,
        "description": "Resource not found",
        "examples": [
            "Drug 'InvalidDrug' not found in catalogue"
        ]
    },
    "CONFLICT": {
        "status": 409,
        "description": "Resource state conflict",
        "examples": [
            "Insufficient stock for 'Ibuprofen'. Available: 5, Requested: 10"
        ]
    },
    "APPLICATION_ERROR": {
        "status": 500,
        "description": "Application error",
        "examples": [
            "Failed to update drug stock",
            "Prescription service unavailable"
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