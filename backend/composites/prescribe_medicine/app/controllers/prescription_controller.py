from flask import jsonify, request
from requests.exceptions import RequestException

from app.clients.base import OrchestrationError, ExternalResponseError
from app.services.prescription_service import PrescribeMedicineService
from utils.exceptions import (
    AppError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from utils.error_handlers import (
    handle_app_error,
    handle_conflict_error,
    handle_generic_error,
    handle_not_found_error,
    handle_request_exception,
    handle_validation_error,
)

service = PrescribeMedicineService()


def prescribe_medicine(record_id: int):
    """
    POST /prescribe/<record_id>
    
    Composite service that orchestrates the prescription workflow:
    1. Fetch clinical record
    2. Get drug catalogue
    3. Update drug stock quantities
    4. Create prescription records
    5. Generate invoice
    
    Request body:
    {
        "items": [
            {
                "drugId": 123,
                "quantity": 2,
                "dosage": "10mg twice daily"
            },
            {
                "drugId": 456,
                "quantity": 1,
                "dosage": "5mg once daily"
            }
        ]
    }
    
    Success Response (201):
    {
        "recordId": 1234,
        "patientId": "P1234",
        "items": [
            {
                "drugId": 123,
                "drugName": "Ibuprofen",
                "quantity": 2,
                "dosage": "10mg twice daily",
                "unitPrice": "10.00",
                "lineTotal": "20.00",
                "prescriptionId": "RX-456"
            }
        ],
        "invoice": {
            "invoiceId": "INV-789",
            ...
        },
        "total": "20.00",
        "status": "success"
    }
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        if "items" not in data:
            raise ValidationError("'items' field is required in request body")

        if not isinstance(data["items"], list):
            raise ValidationError("'items' must be an array")

        if not data["items"]:
            raise ValidationError("'items' array cannot be empty")

        # Validate and normalize each item
        normalized_items = []
        for idx, item in enumerate(data["items"]):
            if not isinstance(item, dict):
                raise ValidationError(f"items[{idx}] must be an object")

            # Check required fields
            required_fields = ["drugId", "quantity", "dosage"]
            missing_fields = [f for f in required_fields if f not in item]
            if missing_fields:
                raise ValidationError(
                    f"items[{idx}] missing required fields: {', '.join(missing_fields)}"
                )

            # Validate and convert drugId
            try:
                drug_id = int(item["drugId"])
                if drug_id <= 0:
                    raise ValueError("drugId must be positive")
            except (TypeError, ValueError):
                raise ValidationError(f"items[{idx}].drugId must be a positive integer")

            # Validate and convert quantity
            try:
                quantity = int(item["quantity"])
                if quantity <= 0:
                    raise ValueError("quantity must be positive")
            except (TypeError, ValueError):
                raise ValidationError(f"items[{idx}].quantity must be a positive integer")

            # Validate dosage
            dosage = str(item["dosage"]).strip()
            if not dosage:
                raise ValidationError(f"items[{idx}].dosage cannot be empty")
            if len(dosage) > 255:
                raise ValidationError(f"items[{idx}].dosage exceeds maximum length")

            normalized_items.append({
                "drugId": drug_id,
                "quantity": quantity,
                "dosage": dosage,
            })

        # Call service to process prescription
        result = service.prescribe_medicine(
            record_id=record_id,
            items=normalized_items,
        )

        # Return success response
        return jsonify({
            "recordId": result["recordId"],
            "patientId": result.get("patientId"),
            "items": result["items"],
            "invoice": result["invoice"],
            "total": result["total"],
            "status": "success"
        }), 201

    except ValidationError as e:
        return handle_validation_error(e)
    except NotFoundError as e:
        return handle_not_found_error(e)
    except ConflictError as e:
        return handle_conflict_error(e)
    except OrchestrationError as e:
        return jsonify({"error": e.error_code, "message": str(e)}), e.status_code
    except ExternalResponseError as e:
        return jsonify({"error": "EXTERNAL_ERROR", "message": str(e)}), 502
    except AppError as e:
        return handle_app_error(e)
    except RequestException as e:
        return handle_request_exception(e)
    except ValueError as e:
        err_response = ValidationError(f"Invalid value: {str(e)}")
        return handle_validation_error(err_response)
    except Exception as e:
        return handle_generic_error(e)
