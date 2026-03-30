from decimal import Decimal

import requests
from requests.exceptions import RequestException

from app.config.settings import (
    CLINICAL_RECORDS_REQUIRED,
    CLINICAL_RECORDS_URL,
    CLINICAL_RECORD_VALIDATE_PATH,
    DRUG_CATALOGUE_URL,
    HTTP_TIMEOUT_SECONDS,
    INVOICE_SERVICE_URL,
    PRESCRIPTION_SERVICE_URL,
)
from utils.exceptions import AppError, ConflictError, NotFoundError, ValidationError


class PrescribeMedicineService:
    def _raise_for_downstream(self, response: requests.Response, fallback_message: str):
        if response.status_code < 400:
            return

        message = fallback_message
        try:
            payload = response.json()
            if isinstance(payload, dict):
                message = payload.get("message") or payload.get("detail") or message
        except Exception:
            pass

        if response.status_code == 404:
            raise NotFoundError(message)
        if response.status_code == 409:
            raise ConflictError(message)
        if response.status_code == 400:
            raise ValidationError(message)

        raise AppError(message)

    def _get_all_drugs(self) -> list[dict]:
        response = requests.get(
            f"{DRUG_CATALOGUE_URL}/drug",
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        self._raise_for_downstream(response, "Failed to fetch drug catalogue")

        drugs = response.json()
        if not isinstance(drugs, list):
            raise AppError("Unexpected response from drug catalogue service")

        return drugs

    def _get_drug_by_id(self, drug_id: int) -> dict:
        response = requests.get(
            f"{DRUG_CATALOGUE_URL}/drug/{drug_id}",
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        self._raise_for_downstream(response, f"Failed to fetch drug {drug_id}")

        drug = response.json()
        if not isinstance(drug, dict):
            raise AppError("Unexpected response from drug catalogue service")

        return drug

    def _restore_stock(self, rollback_updates: list[dict]) -> list[dict]:
        rollback_failures = []

        for update in reversed(rollback_updates):
            try:
                response = requests.put(
                    f"{DRUG_CATALOGUE_URL}/drug/{update['drugId']}",
                    json={"quantity": update["previousQuantity"]},
                    timeout=HTTP_TIMEOUT_SECONDS,
                )

                if response.status_code >= 400:
                    rollback_failures.append(
                        {
                            "drugId": update["drugId"],
                            "message": "Failed to restore stock quantity",
                            "statusCode": response.status_code,
                        }
                    )
            except Exception as e:
                rollback_failures.append(
                    {
                        "drugId": update["drugId"],
                        "message": str(e),
                    }
                )

        return rollback_failures

    def _get_clinical_record(self, record_id: int) -> dict:
        """
        Fetch clinical record from clinical records service.
        Returns dict with: recordId, patientId, date, visitNotes, isClosed
        """
        if not CLINICAL_RECORDS_URL:
            if CLINICAL_RECORDS_REQUIRED:
                raise AppError("Clinical records URL is not configured")
            return None

        try:
            response = requests.get(
                f"{CLINICAL_RECORDS_URL}{CLINICAL_RECORD_VALIDATE_PATH.format(recordId=record_id)}",
                timeout=HTTP_TIMEOUT_SECONDS,
            )
        except RequestException as e:
            if CLINICAL_RECORDS_REQUIRED:
                raise AppError(f"Clinical record service unavailable: {str(e)}")
            return None

        if response.status_code == 404:
            if CLINICAL_RECORDS_REQUIRED:
                raise NotFoundError(f"Clinical record {record_id} not found")
            return None

        if response.status_code >= 400:
            if CLINICAL_RECORDS_REQUIRED:
                self._raise_for_downstream(response, "Failed to fetch clinical record")
            return None

        record = response.json()
        if not isinstance(record, dict):
            raise AppError("Unexpected response format from clinical records service")

        if record.get("isClosed", False):
            raise ConflictError(f"Cannot prescribe for closed clinical record {record_id}")

        return record

    def prescribe_medicine(self, record_id: int, items: list[dict]):
        if not items:
            raise ValidationError("At least one medicine item is required")

        # Step 2: Get clinical record
        clinical_record = self._get_clinical_record(record_id)

        # Step 3: Validate and fetch requested drugs one by one
        prescribed_items = []
        invoice_total = Decimal("0")
        rollback_updates = []

        try:
            # Step 4: Process each prescribed item
            for item in items:
                drug_id = item["drugId"]
                quantity = item["quantity"]
                dosage = item["dosage"]

                drug = self._get_drug_by_id(drug_id)
                current_quantity = int(drug["quantity"])

                if quantity > current_quantity:
                    raise ConflictError(
                        f"Insufficient stock for drug {drug_id}. Available: {current_quantity}, Requested: {quantity}"
                    )

                # Step 4a: Update drug stock via PUT
                update_response = requests.put(
                    f"{DRUG_CATALOGUE_URL}/drug/{drug_id}",
                    json={"quantity": current_quantity - quantity},
                    timeout=HTTP_TIMEOUT_SECONDS,
                )
                self._raise_for_downstream(update_response, f"Failed to update drug stock for drug {drug_id}")

                rollback_updates.append({
                    "drugId": drug_id,
                    "previousQuantity": current_quantity,
                })

                # Step 6: Create prescription record via POST
                # If prescription service is not available, skip this step
                prescription_payload = None
                if PRESCRIPTION_SERVICE_URL:
                    try:
                        prescription_response = requests.post(
                            f"{PRESCRIPTION_SERVICE_URL}/prescription",
                            json={
                                "recordId": record_id,
                                "drugId": drug_id,
                                "quantity": quantity,
                                "dosage": dosage,
                            },
                            timeout=HTTP_TIMEOUT_SECONDS,
                        )
                        self._raise_for_downstream(
                            prescription_response,
                            f"Failed to create prescription for drug {drug_id}",
                        )
                        prescription_payload = prescription_response.json()
                    except Exception as e:
                        # Log but don't fail if prescription service is unavailable
                        print(f"Warning: Prescription service unavailable: {str(e)}")
                else:
                    # Generate a mock prescription if service not configured
                    prescription_payload = {
                        "prescriptionId": f"RX-{record_id}-{drug_id}",
                        "recordId": record_id,
                        "drugId": drug_id,
                        "quantity": quantity,
                        "dosage": dosage
                    }
                item_total = Decimal(str(drug["price"])) * Decimal(quantity)
                invoice_total += item_total

                prescribed_items.append({
                    "drugId": drug_id,
                    "drugName": drug.get("drugName", ""),
                    "quantity": quantity,
                    "dosage": dosage,
                    "unitPrice": str(drug["price"]),
                    "lineTotal": str(item_total),
                    "prescriptionId": prescription_payload.get("prescriptionId"),
                })

            # Step 7: Create invoice via POST
            invoice_response = requests.post(
                f"{INVOICE_SERVICE_URL}/invoice",
                json={
                    "recordId": record_id,
                    "patientId": clinical_record.get("patientId") if clinical_record else None,
                    "prescriptions": [{
                        "drugId": item["drugId"],
                        "quantity": item["quantity"],
                        "dosage": item["dosage"]
                    } for item in prescribed_items],
                    "total": str(invoice_total)
                },
                timeout=HTTP_TIMEOUT_SECONDS,
            )
            self._raise_for_downstream(invoice_response, "Failed to create invoice")

            # Step 8: Return successful result
            return {
                "recordId": record_id,
                "patientId": clinical_record.get("patientId") if clinical_record else None,
                "items": prescribed_items,
                "invoice": invoice_response.json(),
                "total": str(invoice_total),
            }

        except (AppError, RequestException) as e:
            # Rollback: Restore stock quantities
            rollback_failures = self._restore_stock(rollback_updates)

            if rollback_failures:
                raise AppError(
                    f"Prescription failed: {str(e)} | "
                    f"Stock rollback incomplete - manual intervention required: {rollback_failures}"
                )

            raise


