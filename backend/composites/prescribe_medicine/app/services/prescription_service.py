from decimal import Decimal

from app.clients import drug_catalogue_client, prescription_client, invoice_client
from app.clients.base import OrchestrationError, ExternalResponseError
from utils.exceptions import AppError, NotFoundError, ValidationError


class PrescribeMedicineService:
    """
    Orchestrates the prescribe medicine workflow.
    
    This service coordinates multiple atomic services to:
    1. For each drug: lookup by name, update quantity via HTTP PUT
    2. Create prescription with recordId and list of drugs
    3. Compute total price
    4. Create invoice with recordId, totalPrice, paid=false
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
        """
        Process prescription workflow.
        
        Args:
            record_id: Clinical record ID from URL
            items: List of dicts with drugName and quantity
            
        Returns:
            Dict with recordId, drugs list, totalPrice, status
        """
        if not items:
            raise ValidationError("At least one medicine item is required")

        # Track for rollback and response
        drugs_list = []
        total_price = Decimal("0")
        rollback_stock = []
        created_prescription_id = None

        try:
            # Step 1: For each drug, lookup by name and update quantity via HTTP PUT
            for item in items:
                drug_name = item["drugName"]
                quantity = item["quantity"]

                # Get drug details by name
                drug = drug_catalogue_client.get_drug_by_name(drug_name)
                
                if not drug:
                    raise NotFoundError(f"Drug '{drug_name}' not found in catalogue")

                drug_id = drug.get("drugId")
                current_quantity = drug.get("quantity", 0)
                price = Decimal(str(drug.get("price", 0)))

                # Check if sufficient stock
                if current_quantity < quantity:
                    raise ValidationError(
                        f"Insufficient stock for '{drug_name}'. "
                        f"Available: {current_quantity}, Requested: {quantity}"
                    )

                # Calculate new quantity after deduction
                new_quantity = current_quantity - quantity

                # Update drug quantity via HTTP PUT
                drug_catalogue_client.update_drug_quantity(drug_id, new_quantity)

                # Track for potential rollback
                rollback_stock.append({
                    "drugId": drug_id,
                    "deductedAmount": quantity,
                })

                # Calculate line total
                line_total = price * Decimal(quantity)
                total_price += line_total

                # Add to drugs list for prescription and response
                drugs_list.append({
                    "drugId": drug_id,
                    "drugName": drug_name,
                    "quantity": quantity,
                    "unitPrice": str(price),
                    "lineTotal": str(line_total),
                })

            # Step 2: Create prescription with recordId and list of drugs
            prescription = prescription_client.create_prescription(
                record_id=record_id,
                drugs=[{
                    "drugId": d["drugId"],
                    "drugName": d["drugName"],
                    "quantity": d["quantity"],
                } for d in drugs_list]
            )
            created_prescription_id = prescription.get("prescriptionId")

            # Add prescription ID to each drug in response
            for drug in drugs_list:
                drug["prescriptionId"] = created_prescription_id

            # Step 3: Create invoice with recordId, totalPrice, paid=false
            invoice = invoice_client.create_invoice(
                record_id=record_id,
                total_price=str(total_price),
                paid=False
            )

            # Step 4: Return successful result
            return {
                "recordId": record_id,
                "drugs": drugs_list,
                "totalPrice": str(total_price),
                "status": "success",
            }

        except (AppError, OrchestrationError, ExternalResponseError) as e:
            # Rollback: Restore stock AND delete prescriptions
            stock_failures = self._restore_stock(rollback_stock)
            prescription_failures = self._delete_prescriptions(
                [created_prescription_id] if created_prescription_id else []
            )
            all_failures = stock_failures + prescription_failures

            if all_failures:
                raise AppError(
                    f"Prescription failed: {str(e)} | "
                    f"Rollback incomplete - manual intervention required: {all_failures}"
                )

            raise
