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
    1. For each drug: lookup by name, update quantity via HTTP PUT
    2. Create prescription with recordId and list of drugs (drugId, drugName, quantity)
    3. Compute total price
    4. Create invoice with recordId and total
    
    Request body:
    {
        "drugs": [
            {
                "drugName": "Ibuprofen",
                "quantity": 2
            },
            {
                "drugName": "Paracetamol",
                "quantity": 1
            }
        ]
    }
    
    Success Response (201):
    {
        "recordId": 1234,
        "drugs": [
            {
                "drugId": 123,
                "drugName": "Ibuprofen",
                "quantity": 2,
                "unitPrice": "10.00",
                "lineTotal": "20.00",
                "prescriptionId": 456
            }
        ],
        "totalPrice": "20.00",
        "status": "success"
    }
    """
    try:
        data = request.get_json()

        if not data:
            raise ValidationError("Request body is required")

        if "drugs" not in data:
            raise ValidationError("'drugs' field is required in request body")

        if not isinstance(data["drugs"], list):
            raise ValidationError("'drugs' must be an array")

        if not data["drugs"]:
            raise ValidationError("'drugs' array cannot be empty")

        # Validate and normalize each drug
        normalized_drugs = []
        for idx, drug in enumerate(data["drugs"]):
            if not isinstance(drug, dict):
                raise ValidationError(f"drugs[{idx}] must be an object")

            # Check required fields
            required_fields = ["drugName", "quantity"]
            missing_fields = [f for f in required_fields if f not in drug]
            if missing_fields:
                raise ValidationError(
                    f"drugs[{idx}] missing required fields: {', '.join(missing_fields)}"
                )

            # Validate drugName
            drug_name = str(drug["drugName"]).strip()
            if not drug_name:
                raise ValidationError(f"drugs[{idx}].drugName cannot be empty")

            # Validate and convert quantity
            try:
                quantity = int(drug["quantity"])
                if quantity <= 0:
                    raise ValueError("quantity must be positive")
            except (TypeError, ValueError):
                raise ValidationError(f"drugs[{idx}].quantity must be a positive integer")

            normalized_drugs.append({
                "drugName": drug_name,
                "quantity": quantity,
            })

        # Call service to process prescription
        result = service.prescribe_medicine(
            record_id=record_id,
            drugs=normalized_drugs,
        )

        # Return success response
        return jsonify({
            "recordId": result["recordId"],
            "drugs": result["drugs"],
            "totalPrice": result["totalPrice"],
            "status": result["status"]
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
