from decimal import Decimal

from app.clients import drug_catalogue_client, prescription_client, invoice_client, records_client
from app.clients.base import OrchestrationError, ExternalResponseError
from app.config import settings
from utils.exceptions import AppError, ValidationError


class PrescribeMedicineService:
    """
    Orchestrates the prescribe medicine workflow.
    
    This service coordinates multiple atomic services to:
    1. Validate clinical record
    2. Deduct drug stock (atomic)
    3. Create prescription records
    4. Create invoice
    
    On failure, it rolls back both stock and prescriptions.
    """

    def _restore_stock(self, rollback_updates: list[dict]) -> list[dict]:
        """Restore stock for rollback using the atomic restore endpoint."""
        failures = []

        for update in reversed(rollback_updates):
            try:
                drug_catalogue_client.restore_stock(
                    update["drugId"],
                    update["deductedAmount"]
                )
            except Exception as e:
                failures.append({
                    "drugId": update["drugId"],
                    "type": "stock",
                    "message": str(e),
                })

        return failures

    def _delete_prescriptions(self, prescription_ids: list[int]) -> list[dict]:
        """Delete created prescriptions for rollback."""
        failures = []

        for pid in reversed(prescription_ids):
            if pid is None:
                continue
            try:
                prescription_client.delete_prescription(pid)
            except Exception as e:
                failures.append({
                    "prescriptionId": pid,
                    "type": "prescription",
                    "message": str(e),
                })

        return failures

    def prescribe_medicine(self, record_id: int, items: list[dict]):
        if not items:
            raise ValidationError("At least one medicine item is required")

        # Step 1: Get and validate clinical record
        clinical_record = records_client.get_clinical_record(
            record_id,
            required=settings.CLINICAL_RECORDS_REQUIRED
        )

        # Track items for rollback
        prescribed_items = []
        invoice_total = Decimal("0")
        rollback_stock = []
        created_prescription_ids = []

        try:
            # Step 2: Process each prescribed item
            for item in items:
                drug_id = item["drugId"]
                quantity = item["quantity"]
                dosage = item["dosage"]

                # Step 2a: Atomically deduct drug stock
                drug = drug_catalogue_client.deduct_stock(drug_id, quantity)

                rollback_stock.append({
                    "drugId": drug_id,
                    "deductedAmount": quantity,
                })

                # Step 2b: Create prescription record
                prescription = prescription_client.create_prescription(
                    record_id=record_id,
                    drug_id=drug_id,
                    quantity=quantity,
                    dosage=dosage,
                )
                created_prescription_ids.append(prescription.get("prescriptionId"))

                # Calculate totals
                item_total = Decimal(str(drug["price"])) * Decimal(quantity)
                invoice_total += item_total

                prescribed_items.append({
                    "drugId": drug_id,
                    "drugName": drug.get("drugName", ""),
                    "quantity": quantity,
                    "dosage": dosage,
                    "unitPrice": str(drug["price"]),
                    "lineTotal": str(item_total),
                    "prescriptionId": prescription.get("prescriptionId"),
                })

            # Step 3: Create invoice
            invoice = invoice_client.create_invoice(record_id, str(invoice_total))

            # Step 4: Return successful result
            return {
                "recordId": record_id,
                "patientId": clinical_record.get("patientId") if clinical_record else None,
                "items": prescribed_items,
                "invoice": invoice,
                "total": str(invoice_total),
            }

        except (AppError, OrchestrationError, ExternalResponseError) as e:
            # Rollback: Restore stock AND delete prescriptions (FIX-5)
            stock_failures = self._restore_stock(rollback_stock)
            prescription_failures = self._delete_prescriptions(created_prescription_ids)
            all_failures = stock_failures + prescription_failures

            if all_failures:
                raise AppError(
                    f"Prescription failed: {str(e)} | "
                    f"Rollback incomplete - manual intervention required: {all_failures}"
                )

            raise
