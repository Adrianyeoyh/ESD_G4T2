# Code Review Implementation Plan

## Prescribe Medicine Orchestrator + Drug Catalogue + Prescription Service

**Date:** 2026-03-30
**Branch:** `prescribe_meds`
**Reviewed by:** Code Review Agent
**Status:** Pending Implementation

---

## Table of Contents

1. [Issue Summary](#issue-summary)
2. [Prescribe Medicine Orchestrator Fixes](#1-prescribe-medicine-orchestrator)
3. [Drug Catalogue Service Fixes](#2-drug-catalogue-service)
4. [Prescription Service Fixes](#3-prescription-service)
5. [Cross-Service Fixes](#4-cross-service-fixes)
6. [Implementation Order](#5-implementation-order)

---

## Issue Summary

| Priority | Count | Description |
|----------|-------|-------------|
| CRITICAL | 7 | Will crash, corrupt data, or break in production |
| HIGH | 12 | Incorrect behavior, missing rollback, architectural gaps |
| MEDIUM | 10 | Missing observability, inconsistency, code quality |
| **Total** | **29** | |

---

## 1. Prescribe Medicine Orchestrator

**Location:** `backend/composites/prescribe_medicine/`

---

### FIX-1: Delete dead `db.py` that crashes on import [CRITICAL]

**File:** `app/config/db.py`
**Problem:** Imports `DATABASE_URL` from `app.config.settings`, but `settings.py` has no such variable. If any code imports `db.py`, the service crashes with `ImportError`. The file also references `invoice_schema` search path (copy-pasted from invoice service). This is a pure orchestrator with no database.

**Current code:**
```python
# app/config/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import DATABASE_URL  # DOES NOT EXIST

engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-csearch_path=invoice_schema"}  # Wrong schema
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
```

**Fix:** Delete the entire file.

```bash
rm backend/composites/prescribe_medicine/app/config/db.py
```

---

### FIX-2: Delete placeholder model and repository files [CRITICAL]

**Files:**
- `app/models/prescription_model.py` — Contains only a docstring: "This composite does not use local SQLAlchemy models."
- `app/repositories/prescription_repository.py` — Contains only a docstring: "This composite does not use a local repository layer."

**Problem:** These files mislead developers into thinking there's a persistence layer. The `make_payment` composite has **no** `models/` or `repositories/` directories — only `clients/`, `controllers/`, `routes/`, `services/`, and `config/`.

**Fix:** Delete both files and their parent directories.

```bash
rm backend/composites/prescribe_medicine/app/models/prescription_model.py
rm backend/composites/prescribe_medicine/app/repositories/prescription_repository.py
rmdir backend/composites/prescribe_medicine/app/models
rmdir backend/composites/prescribe_medicine/app/repositories
```

---

### FIX-3: Invoice API payload mismatch [CRITICAL]

**File:** `app/services/prescription_service.py` lines 233-246
**Problem:** The orchestrator sends `patientId` and `prescriptions` in the invoice creation payload, but `InvoiceCreate` (in `invoice_service/app/schemas/invoice_schema.py`) only accepts `record_id` and `total`. Pydantic's default behavior silently ignores extra fields, so this doesn't crash, but the data is never stored. The orchestrator thinks it's linking prescriptions to the invoice, but it isn't.

**Current code:**
```python
invoice_response = requests.post(
    f"{INVOICE_SERVICE_URL}/invoice",
    json={
        "recordId": record_id,
        "patientId": clinical_record.get("patientId") if clinical_record else None,  # IGNORED
        "prescriptions": [{...}],  # IGNORED
        "total": str(invoice_total)
    },
    timeout=HTTP_TIMEOUT_SECONDS,
)
```

**InvoiceCreate schema only accepts:**
```python
class InvoiceCreate(BaseModel):
    record_id: int
    total: Decimal
```

**Fix:** Remove the extra fields from the payload to avoid confusion. The invoice is linked to prescriptions via `record_id`.

```python
# app/services/prescription_service.py — lines 233-246
invoice_response = requests.post(
    f"{INVOICE_SERVICE_URL}/invoice",
    json={
        "recordId": record_id,
        "total": str(invoice_total),
    },
    timeout=HTTP_TIMEOUT_SECONDS,
)
```

---

### FIX-4: Race condition on stock check-then-deduct [CRITICAL]

**File:** `app/services/prescription_service.py` lines 191-205
**Problem:** The orchestrator GETs the current stock, checks quantity locally, then PATCHes the new quantity. Between the GET and PATCH, another concurrent request can deduct the same stock, resulting in negative inventory.

**Current flow (unsafe):**
```
Request A: GET /drug/1 → quantity=10
Request B: GET /drug/1 → quantity=10
Request A: 5 <= 10? yes → PATCH quantity=5
Request B: 5 <= 10? yes → PATCH quantity=5   # Should be 0, not 5!
```

**Fix — Option A (recommended): Add a `PATCH /drug/{id}/deduct` endpoint to drug_catalogue**

This new endpoint atomically checks stock and deducts in a single DB transaction:

```python
# drug_catalogue_service/app/services/drug_catalogue_service.py — new method
def deduct_quantity(self, drug_id: int, amount: int):
    """Atomically deduct stock. Raises ConflictError if insufficient."""
    if amount <= 0:
        raise ValidationError("Deduction amount must be positive")

    drug = self.get_drug(drug_id)
    if drug.quantity < amount:
        raise ConflictError(
            f"Insufficient stock for drug {drug_id}. "
            f"Available: {drug.quantity}, Requested: {amount}"
        )
    drug.quantity -= amount
    self.db.commit()
    self.db.refresh(drug)
    return drug
```

```python
# drug_catalogue_service/app/routers/drug_catalogue_router.py — new endpoint
@router.patch("/{drug_id}/deduct", response_model=DrugResponse)
def deduct_drug_quantity(
    drug_id: int,
    body: DrugDeductQuantity,
    service: DrugService = Depends(get_drug_service),
):
    return service.deduct_quantity(drug_id, body.amount)
```

```python
# drug_catalogue_service/app/schemas/drug_catalogue_schema.py — new schema
class DrugDeductQuantity(DrugBase):
    amount: int

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Amount must be a positive integer")
        return v
```

Then update the orchestrator to use it:

```python
# prescribe_medicine/app/services/prescription_service.py
# Replace the GET-check-PATCH pattern with a single call:
drug = self._get_drug_by_id(drug_id)  # Still fetch for price/name info
deduct_response = requests.patch(
    f"{DRUG_CATALOGUE_URL}/drug/{drug_id}/deduct",
    json={"amount": quantity},
    timeout=HTTP_TIMEOUT_SECONDS,
)
self._raise_for_downstream(deduct_response, f"Failed to deduct stock for drug {drug_id}")
```

**Fix — Option B (simpler): Use DB-level constraint**

If adding a new endpoint is too heavy, at minimum add a DB-level `CHECK (quantity >= 0)` constraint on the drug table (already exists as `ck_quantity_non_negative`), and catch the IntegrityError in `update_quantity()`:

```python
# drug_catalogue_service/app/services/drug_catalogue_service.py
def update_quantity(self, drug_id: int, new_quantity: int):
    if new_quantity < 0:
        raise ValidationError("Quantity must be a non-negative integer")
    drug = self.get_drug(drug_id)
    drug.quantity = new_quantity
    try:
        self.db.commit()
    except IntegrityError:
        self.db.rollback()
        raise ConflictError(f"Cannot set quantity to {new_quantity} for drug {drug_id}")
    self.db.refresh(drug)
    return drug
```

---

### FIX-5: No prescription rollback on invoice failure [HIGH]

**File:** `app/services/prescription_service.py` lines 258-268
**Problem:** When invoice creation fails (step 7), the rollback only restores drug stock quantities. The prescription records created in step 6 are left orphaned in the database — they exist with no corresponding invoice.

**Current rollback:**
```python
except (AppError, RequestException) as e:
    rollback_failures = self._restore_stock(rollback_updates)  # Only restores stock
    ...
```

**Fix:** Track prescription IDs and delete them during rollback.

```python
# app/services/prescription_service.py

def _delete_prescriptions(self, prescription_ids: list[int]) -> list[dict]:
    """Rollback: delete created prescriptions."""
    failures = []
    for pid in reversed(prescription_ids):
        try:
            response = requests.delete(
                f"{PRESCRIPTION_SERVICE_URL}/prescription/{pid}",
                timeout=HTTP_TIMEOUT_SECONDS,
            )
            if response.status_code >= 400 and response.status_code != 404:
                failures.append({
                    "prescriptionId": pid,
                    "message": "Failed to delete prescription",
                    "statusCode": response.status_code,
                })
        except Exception as e:
            failures.append({
                "prescriptionId": pid,
                "message": str(e),
            })
    return failures
```

Then in `prescribe_medicine()`, track IDs and call both rollback methods:

```python
# In the main orchestration loop, track prescription IDs:
created_prescription_ids = []

# After creating each prescription (line ~213-218):
prescription_payload = self._create_prescription(...)
created_prescription_ids.append(prescription_payload.get("prescriptionId"))

# In the except block (line ~258):
except (AppError, RequestException) as e:
    stock_failures = self._restore_stock(rollback_updates)
    prescription_failures = self._delete_prescriptions(created_prescription_ids)
    all_failures = stock_failures + prescription_failures

    if all_failures:
        raise AppError(
            f"Prescription failed: {str(e)} | "
            f"Rollback incomplete - manual intervention required: {all_failures}"
        )
    raise
```

---

### FIX-6: Create client abstraction layer [HIGH]

**Problem:** The orchestrator makes ~15 raw `requests.get/post/patch` calls directly in the service layer. The `make_payment` composite uses a clean `app/clients/` directory with a shared `base.py` HTTP helper and dedicated client modules.

**Fix:** Create the following client structure:

```
app/clients/
    __init__.py
    base.py                  # Shared HTTP helper (adapt from make_payment)
    drug_catalogue_client.py # get_drug(), get_all_drugs(), deduct_stock(), restore_stock()
    prescription_client.py   # create_prescription(), delete_prescription()
    invoice_client.py        # create_invoice()
    records_client.py        # get_clinical_record()
```

**`app/clients/base.py`** — Adapt from make_payment's base.py:

```python
import logging
import requests
from app.config.settings import HTTP_TIMEOUT_SECONDS
from utils.exceptions import AppError, NotFoundError, ConflictError, ValidationError

logger = logging.getLogger(__name__)


def http_request(method: str, url: str, json_body: dict | None = None) -> dict:
    """Make an HTTP request to a downstream microservice.

    Returns parsed JSON on 2xx.
    Raises typed exceptions on error status codes.
    """
    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_body,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AppError(f"Dependency call failed: {url}") from exc

    if 200 <= response.status_code < 300:
        if response.content:
            return response.json()
        return {}

    # Parse error payload
    payload = {}
    try:
        payload = response.json()
    except ValueError:
        payload = {"error": response.text}

    message = (
        payload.get("error")
        or payload.get("message")
        or payload.get("detail")
        or f"Request to {url} failed with status {response.status_code}"
    )

    if response.status_code == 404:
        raise NotFoundError(message)
    if response.status_code == 409:
        raise ConflictError(message)
    if response.status_code == 400:
        raise ValidationError(message)

    raise AppError(message)
```

**`app/clients/drug_catalogue_client.py`:**

```python
from app.config.settings import DRUG_CATALOGUE_URL
from app.clients.base import http_request


def get_drug(drug_id: int) -> dict:
    return http_request("GET", f"{DRUG_CATALOGUE_URL}/drug/{drug_id}")


def get_all_drugs() -> list[dict]:
    result = http_request("GET", f"{DRUG_CATALOGUE_URL}/drug")
    if not isinstance(result, list):
        from utils.exceptions import AppError
        raise AppError("Unexpected response from drug catalogue service")
    return result


def deduct_stock(drug_id: int, amount: int) -> dict:
    return http_request("PATCH", f"{DRUG_CATALOGUE_URL}/drug/{drug_id}/deduct", {"amount": amount})


def restore_stock(drug_id: int, quantity: int) -> dict:
    return http_request("PATCH", f"{DRUG_CATALOGUE_URL}/drug/{drug_id}/quantity", {"quantity": quantity})
```

**`app/clients/prescription_client.py`:**

```python
from app.config.settings import PRESCRIPTION_SERVICE_URL
from app.clients.base import http_request
from utils.exceptions import AppError


def create_prescription(record_id: int, drug_id: int, quantity: int, dosage: str) -> dict:
    service_url = (PRESCRIPTION_SERVICE_URL or "").strip()
    if not service_url:
        raise AppError("Prescription service URL is not configured")

    return http_request("POST", f"{service_url}/prescription", {
        "recordId": record_id,
        "drugId": drug_id,
        "quantity": quantity,
        "dosage": dosage,
    })


def delete_prescription(prescription_id: int) -> None:
    service_url = (PRESCRIPTION_SERVICE_URL or "").strip()
    if not service_url:
        raise AppError("Prescription service URL is not configured")

    http_request("DELETE", f"{service_url}/prescription/{prescription_id}")
```

**`app/clients/invoice_client.py`:**

```python
from app.config.settings import INVOICE_SERVICE_URL
from app.clients.base import http_request


def create_invoice(record_id: int, total: str) -> dict:
    return http_request("POST", f"{INVOICE_SERVICE_URL}/invoice", {
        "recordId": record_id,
        "total": total,
    })
```

**`app/clients/records_client.py`:**

```python
from app.config.settings import CLINICAL_RECORDS_URL, CLINICAL_RECORD_VALIDATE_PATH
from app.clients.base import http_request


def get_clinical_record(record_id: int) -> dict:
    url = f"{CLINICAL_RECORDS_URL}{CLINICAL_RECORD_VALIDATE_PATH.format(recordId=record_id)}"
    return http_request("GET", url)
```

Then refactor `prescription_service.py` to use these clients instead of raw `requests` calls.

---

### FIX-7: Remove unused `InvoiceStatus` enum [HIGH]

**File:** `common/tools.py`
**Problem:** Defines `InvoiceStatus` enum that is never imported or used anywhere in the orchestrator. Copy-pasted from make_payment.

**Fix:** Delete the file or remove the unused enum.

```bash
rm backend/composites/prescribe_medicine/common/tools.py
```

If `common/__init__.py` is also empty, remove the directory:
```bash
rm backend/composites/prescribe_medicine/common/__init__.py
rmdir backend/composites/prescribe_medicine/common
```

---

### FIX-8: Register Flask error handlers in app factory [HIGH]

**File:** `app/__init__.py`
**Problem:** The current app factory only registers the blueprint. If any exception escapes the controller's try/except block, Flask returns an HTML error page. The `make_payment` composite properly registers `@app.errorhandler` decorators.

**Current code:**
```python
def create_app():
    app = Flask(__name__)
    app.register_blueprint(prescribe_medicine_bp)
    return app
```

**Fix:** Register error handlers following make_payment's pattern:

```python
import logging
from flask import Flask, jsonify
from app.routes.prescription_routes import prescribe_medicine_bp
from utils.exceptions import AppError, ValidationError, NotFoundError, ConflictError

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.register_blueprint(prescribe_medicine_bp)
    _register_error_handlers(app)
    return app


def _register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(exc):
        return jsonify({"message": exc.message, "error": "VALIDATION_ERROR"}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(exc):
        return jsonify({"message": exc.message, "error": "NOT_FOUND"}), 404

    @app.errorhandler(ConflictError)
    def handle_conflict_error(exc):
        return jsonify({"message": exc.message, "error": "CONFLICT"}), 409

    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return jsonify({"message": exc.message, "error": "APPLICATION_ERROR"}), exc.status_code

    @app.errorhandler(Exception)
    def handle_generic_error(exc):
        logger.exception("Unhandled exception: %s", exc)
        return jsonify({"message": "Internal server error", "error": "INTERNAL_SERVER_ERROR"}), 500
```

---

### FIX-9: Remove unused `schemas.py` validation classes [MEDIUM]

**File:** `app/schemas/schemas.py`
**Problem:** This file defines `MedicinePrescriptionItem`, `PrescribeMedicineRequest`, etc. with validation logic, but the controller (`prescription_controller.py`) does its own inline validation and never imports these schemas. The file is 179 lines of dead code.

**Fix:** Either delete the file and keep the controller's inline validation, or refactor the controller to use these schemas. Since the controller validation is thorough and already working, deleting the unused schemas is cleaner:

```bash
rm backend/composites/prescribe_medicine/app/schemas/schemas.py
rm backend/composites/prescribe_medicine/app/schemas/__init__.py
rmdir backend/composites/prescribe_medicine/app/schemas
```

---

### FIX-10: Add health check endpoint [MEDIUM]

**Problem:** No `/health` endpoint. Docker and Kubernetes cannot health-check the service. The `make_payment` composite has a health endpoint.

**Fix:** Add to `app/routes/prescription_routes.py`:

```python
from flask import Blueprint, jsonify
from app.controllers.prescription_controller import prescribe_medicine

prescribe_medicine_bp = Blueprint("prescribe_medicine_bp", __name__)


@prescribe_medicine_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@prescribe_medicine_bp.route("/prescribe/<int:record_id>", methods=["POST"])
def prescribe(record_id):
    return prescribe_medicine(record_id)
```

---

### FIX-11: Add logging throughout the service [MEDIUM]

**Problem:** Zero `logging` calls anywhere. Failures are completely silent. No way to debug production issues.

**Fix:** Add logging to key points in the service. Example for `prescription_service.py`:

```python
import logging
logger = logging.getLogger(__name__)

class PrescribeMedicineService:
    def prescribe_medicine(self, record_id: int, items: list[dict]):
        logger.info("Starting prescription for record_id=%d with %d items", record_id, len(items))
        # ... existing code ...
        logger.info("Successfully prescribed %d items for record_id=%d, total=%s",
                     len(prescribed_items), record_id, invoice_total)
        return result

    # In the except block:
    except (AppError, RequestException) as e:
        logger.error("Prescription failed for record_id=%d: %s", record_id, str(e))
        rollback_failures = self._restore_stock(rollback_updates)
        if rollback_failures:
            logger.critical("Stock rollback incomplete for record_id=%d: %s",
                           record_id, rollback_failures)
```

Also add to `app/__init__.py`:
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

---

### FIX-12: Remove `ServiceUnavailableError` and `InternalServerError` from exceptions [MEDIUM]

**File:** `utils/exceptions.py`
**Problem:** `ServiceUnavailableError` (503) and `InternalServerError` (500) are defined but never raised anywhere in the codebase. `InternalServerError` is redundant with the base `AppError` which also defaults to 500.

**Fix:** Remove the unused exception classes:

```python
# utils/exceptions.py — keep only these
class AppError(Exception):
    status_code = 500
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class NotFoundError(AppError):
    status_code = 404

class ValidationError(AppError):
    status_code = 400

class ConflictError(AppError):
    status_code = 409
```

Also update `utils/error_handlers.py` to remove the import of `ServiceUnavailableError`.

---

## 2. Drug Catalogue Service

**Location:** `backend/services/drug_catalogue_service/`

---

### FIX-13: Catch `IntegrityError` in `add_drug()` and `update_drug()` [HIGH]

**File:** `app/services/drug_catalogue_service.py` lines 23-38, 40-55
**Problem:** `add_drug()` checks for duplicate names then creates, but this is a check-then-act race condition. If two concurrent requests submit the same drug name, both pass the check, and one gets an unhandled `IntegrityError` from the DB unique constraint — resulting in a 500 instead of a proper 409.

Same issue in `update_drug()` — the duplicate name check is not atomic.

**Current code:**
```python
def add_drug(self, drug_data: DrugCreate):
    existing_drug = self.repo.get_by_name(drug_data.drug_name)
    if existing_drug:
        raise ConflictError(...)
    drug = self.repo.create(...)
    self.db.commit()       # Can throw IntegrityError — NOT CAUGHT
    self.db.refresh(drug)
    return drug
```

**Fix:** Wrap commit in try/except for both methods:

```python
def add_drug(self, drug_data: DrugCreate):
    existing_drug = self.repo.get_by_name(drug_data.drug_name)
    if existing_drug:
        raise ConflictError(
            f"Drug with name '{drug_data.drug_name}' already exists in catalogue"
        )

    drug = self.repo.create(drug_data.drug_name, drug_data.quantity, drug_data.price)
    try:
        self.db.commit()
    except IntegrityError:
        self.db.rollback()
        raise ConflictError(
            f"Drug with name '{drug_data.drug_name}' already exists in catalogue"
        )
    self.db.refresh(drug)
    return drug


def update_drug(self, drug_id: int, update_data: DrugUpdate):
    drug = self.get_drug(drug_id)

    if update_data.drug_name != drug.drug_name:
        existing = self.repo.get_by_name(update_data.drug_name)
        if existing and existing.drug_id != drug_id:
            raise ConflictError(
                f"Drug with name '{update_data.drug_name}' already exists in catalogue"
            )

    drug.drug_name = update_data.drug_name
    drug.quantity = update_data.quantity
    drug.price = update_data.price
    try:
        self.db.commit()
    except IntegrityError:
        self.db.rollback()
        raise ConflictError(
            f"Drug with name '{update_data.drug_name}' already exists in catalogue"
        )
    self.db.refresh(drug)
    return drug
```

Add import at the top of the file:
```python
from sqlalchemy.exc import IntegrityError
```

---

### FIX-14: Add pagination to `GET /drug` [HIGH]

**File:** `app/routers/drug_catalogue_router.py`, `app/services/drug_catalogue_service.py`, `app/repositories/drug_catalogue_repository.py`
**Problem:** `list_all()` returns every drug in the table with no limit. Will cause memory and performance issues as the catalogue grows.

**Fix:**

```python
# app/repositories/drug_catalogue_repository.py — add pagination
def list_all(self, skip: int = 0, limit: int = 100) -> list[Drug]:
    return self.db.query(Drug).offset(skip).limit(limit).all()
```

```python
# app/services/drug_catalogue_service.py
def list_drugs(self, skip: int = 0, limit: int = 100):
    return self.repo.list_all(skip=skip, limit=limit)
```

```python
# app/routers/drug_catalogue_router.py
from fastapi import Query

@router.get("", response_model=list[DrugResponse])
def get_all_drugs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: DrugService = Depends(get_drug_service),
):
    return service.list_drugs(skip=skip, limit=limit)
```

---

### FIX-15: Add atomic stock deduction endpoint [HIGH]

**File:** `app/routers/drug_catalogue_router.py`, `app/services/drug_catalogue_service.py`, `app/schemas/drug_catalogue_schema.py`
**Problem:** Required by FIX-4 (orchestrator race condition). The drug catalogue needs an endpoint that atomically checks and deducts stock.

**Fix:** See FIX-4 Option A above for the complete implementation. Summary:

1. Add `DrugDeductQuantity` schema with `amount: int` field
2. Add `deduct_quantity()` method to `DrugService`
3. Add `PATCH /drug/{drug_id}/deduct` route

---

### FIX-16: Add health check endpoint [MEDIUM]

**File:** `app/__init__.py` or new health router
**Problem:** No `/health` endpoint for container orchestration.

**Fix:** Add a health router in `app/__init__.py`:

```python
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
```

Or add it inline in `create_app()`:
```python
def create_app() -> FastAPI:
    app = FastAPI(...)

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    # ... rest of setup
```

---

### FIX-17: Add logging [MEDIUM]

**Problem:** Zero logging throughout the service. No visibility into operations.

**Fix:** Add logging to the service layer:

```python
# app/services/drug_catalogue_service.py
import logging
logger = logging.getLogger(__name__)

class DrugService:
    def add_drug(self, drug_data: DrugCreate):
        logger.info("Creating drug: name=%s, quantity=%d, price=%s",
                     drug_data.drug_name, drug_data.quantity, drug_data.price)
        # ... existing code ...
        logger.info("Created drug: id=%d, name=%s", drug.drug_id, drug.drug_name)
        return drug

    def update_quantity(self, drug_id: int, new_quantity: int):
        logger.info("Updating drug %d quantity to %d", drug_id, new_quantity)
        # ... existing code ...
        return drug

    def delete_drug(self, drug_id: int):
        logger.info("Deleting drug: id=%d", drug_id)
        # ... existing code ...
```

---

### FIX-18: Catch `IntegrityError` in `delete_drug()` [MEDIUM]

**File:** `app/services/drug_catalogue_service.py` line 67-70
**Problem:** If the drug is referenced by other records (even without FK constraints, future additions could add them), the delete commit has no error handling.

**Fix:**
```python
def delete_drug(self, drug_id: int):
    drug = self.get_drug(drug_id)
    self.repo.delete(drug)
    try:
        self.db.commit()
    except IntegrityError:
        self.db.rollback()
        raise ConflictError(f"Cannot delete drug {drug_id} — it is referenced by existing records")
```

---

## 3. Prescription Service

**Location:** `backend/services/prescription_service/`

---

### FIX-19: Fix `reload=True` hardcoded in production [CRITICAL]

**File:** `run.py`
**Problem:** Uvicorn runs with `reload=True` always, including in Docker/production. This causes file-watching overhead, unexpected restarts, and connection drops.

**Current code:**
```python
uvicorn.run("app:app", host="0.0.0.0", port=5005, reload=True)
```

**Fix:**
```python
import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5005,
        reload=(os.getenv("APP_ENV", "local") != "docker"),
    )
```

---

### FIX-20: Remove or guard `get_next_record_id()` [HIGH]

**File:** `app/repositories/prescription_repository.py` lines 25-27
**Problem:** Auto-generating record IDs via `MAX(recordId) + 1` is:
1. **Not atomic** — two concurrent calls get the same ID
2. **Semantically wrong** — record IDs should come from the clinical records service, not be invented by the prescription service
3. **Creates phantom records** — prescriptions linked to record IDs that don't exist in the records system

**Current code:**
```python
def get_next_record_id(self) -> int:
    current_max = self.db.query(func.max(Prescription.record_id)).scalar()
    return (current_max or 0) + 1
```

**Fix:** Make `record_id` required in `PrescriptionCreate` and remove auto-generation:

```python
# app/schemas/prescription_schema.py
class PrescriptionCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    record_id: int  # REQUIRED, not Optional
    drug_id: int
    quantity: int
    dosage: str = Field(min_length=1, max_length=255)

    @field_validator("record_id", "drug_id")
    @classmethod
    def validate_positive_ids(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ID values must be positive integers")
        return v
    # ... rest unchanged
```

```python
# app/services/prescription_service.py
def assign_prescription(self, prescription_data: PrescriptionCreate):
    if prescription_data.quantity <= 0:
        raise ValidationError("Quantity must be greater than 0")
    if prescription_data.drug_id <= 0:
        raise ValidationError("drugId must be a positive integer")
    if prescription_data.record_id <= 0:
        raise ValidationError("recordId must be a positive integer")

    prescription = self.repo.create(
        prescription_data.record_id,  # Always use the provided record_id
        prescription_data.drug_id,
        prescription_data.quantity,
        prescription_data.dosage,
    )
    # ... rest unchanged
```

Remove `get_next_record_id()` from the repository.

---

### FIX-21: Add error handling to `delete_prescription()` [HIGH]

**File:** `app/services/prescription_service.py` lines 71-74
**Problem:** Unlike `assign_prescription` and `update_prescription` which catch `IntegrityError`, `delete_prescription` has no error handling on commit.

**Current code:**
```python
def delete_prescription(self, prescription_id: int):
    prescription = self.get_prescription(prescription_id)
    self.repo.delete(prescription)
    self.db.commit()  # No try/except
```

**Fix:**
```python
def delete_prescription(self, prescription_id: int):
    prescription = self.get_prescription(prescription_id)
    self.repo.delete(prescription)
    try:
        self.db.commit()
    except IntegrityError:
        self.db.rollback()
        raise ConflictError(
            f"Cannot delete prescription {prescription_id} — integrity constraint violated"
        )
```

---

### FIX-22: Add pagination to `GET /prescription` [HIGH]

**File:** `app/routers/prescription_router.py`, `app/services/prescription_service.py`, `app/repositories/prescription_repository.py`
**Problem:** `list_all()` returns every prescription with no limit.

**Fix:** Same pattern as FIX-14:

```python
# app/repositories/prescription_repository.py
def list_all(self, skip: int = 0, limit: int = 100) -> list[Prescription]:
    return self.db.query(Prescription).offset(skip).limit(limit).all()
```

```python
# app/services/prescription_service.py
def list_prescriptions(self, skip: int = 0, limit: int = 100) -> list:
    return self.repo.list_all(skip=skip, limit=limit)
```

```python
# app/routers/prescription_router.py
from fastapi import Query

@router.get("", response_model=list[PrescriptionResponse])
def list_prescriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: PrescriptionService = Depends(get_prescription_service),
):
    return service.list_prescriptions(skip=skip, limit=limit)
```

---

### FIX-23: Remove duplicate validation in service layer [MEDIUM]

**File:** `app/services/prescription_service.py` lines 25-32
**Problem:** The Pydantic schema already validates `quantity > 0`, `drug_id > 0`, and `record_id > 0` via `@field_validator`. The service layer repeats these same checks. If validation rules change, they must be updated in two places.

**Current (redundant) service code:**
```python
def assign_prescription(self, prescription_data: PrescriptionCreate):
    if prescription_data.quantity <= 0:          # Already validated by schema
        raise ValidationError("Quantity must be greater than 0")
    if prescription_data.drug_id <= 0:           # Already validated by schema
        raise ValidationError("drugId must be a positive integer")
    if prescription_data.record_id is not None and prescription_data.record_id <= 0:  # Already validated
        raise ValidationError("recordId must be a positive integer when provided")
```

**Fix:** Remove the redundant checks from the service. The schema validators will reject invalid data before it reaches the service. After applying FIX-20 (making record_id required):

```python
def assign_prescription(self, prescription_data: PrescriptionCreate):
    # Schema validates quantity > 0, drug_id > 0, record_id > 0
    prescription = self.repo.create(
        prescription_data.record_id,
        prescription_data.drug_id,
        prescription_data.quantity,
        prescription_data.dosage,
    )
    try:
        self.db.commit()
    except IntegrityError:
        self.db.rollback()
        raise ValidationError("Invalid prescription data. Check quantity and dosage values.")
    self.db.refresh(prescription)
    return prescription
```

---

### FIX-24: Add health check endpoint [MEDIUM]

**File:** `app/__init__.py`
**Problem:** No `/health` endpoint.

**Fix:** Same as FIX-16:
```python
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
```

---

### FIX-25: Add logging [MEDIUM]

**Problem:** Zero logging throughout the service.

**Fix:** Add logging to service methods:

```python
import logging
logger = logging.getLogger(__name__)

class PrescriptionService:
    def assign_prescription(self, prescription_data: PrescriptionCreate):
        logger.info("Creating prescription: record_id=%s, drug_id=%d, quantity=%d",
                     prescription_data.record_id, prescription_data.drug_id,
                     prescription_data.quantity)
        # ... existing code ...
        logger.info("Created prescription: id=%d", prescription.prescription_id)
        return prescription

    def delete_prescription(self, prescription_id: int):
        logger.info("Deleting prescription: id=%d", prescription_id)
        # ... existing code ...
```

---

### FIX-26: Add `GET /prescription/record/{record_id}` endpoint [MEDIUM]

**Problem:** The orchestrator creates prescriptions linked to a `record_id`, but there's no way to query prescriptions by record. This is needed for the frontend to display all prescriptions for a clinical visit.

**Fix:**

```python
# app/repositories/prescription_repository.py — new method
def get_by_record_id(self, record_id: int) -> list[Prescription]:
    return self.db.query(Prescription).filter(
        Prescription.record_id == record_id
    ).all()
```

```python
# app/services/prescription_service.py — new method
def get_prescriptions_by_record(self, record_id: int) -> list:
    if record_id <= 0:
        raise ValidationError("Record ID must be a positive integer")
    return self.repo.get_by_record_id(record_id)
```

```python
# app/routers/prescription_router.py — new endpoint
@router.get("/record/{record_id}", response_model=list[PrescriptionResponse])
def get_prescriptions_by_record(
    record_id: int,
    service: PrescriptionService = Depends(get_prescription_service),
):
    return service.get_prescriptions_by_record(record_id)
```

---

## 4. Cross-Service Fixes

---

### FIX-27: Standardize error response format across services [MEDIUM]

**Problem:** The three services use different error response formats:

| Service | Format |
|---------|--------|
| Drug Catalogue (FastAPI) | `{"success": false, "data": null, "error": "..."}` |
| Prescription (FastAPI) | `{"success": false, "data": null, "error": "..."}` |
| Prescribe Medicine (Flask) | `{"message": "...", "error": "ERROR_CODE"}` |
| Make Payment (Flask) | `{"success": false, "data": null, "error": "...", "errorCode": "..."}` |

The orchestrator's `_raise_for_downstream()` tries to parse multiple formats, which is fragile.

**Fix:** Align the orchestrator's error format to match make_payment's format:

```python
# prescribe_medicine error handlers should return:
{
    "success": false,
    "data": null,
    "error": "Human-readable message",
    "errorCode": "VALIDATION_ERROR"
}
```

Update `utils/error_handlers.py` in prescribe_medicine to use this format, or better yet, use the registered Flask error handlers from FIX-8 which already follow this pattern.

---

### FIX-28: Add database indexes on prescription foreign key columns [MEDIUM]

**File:** `db/init.sql`
**Problem:** The prescription table has `recordId` and `drugId` columns but no indexes. Queries filtering by these columns will be slow on large datasets.

**Fix:** Add indexes to the init SQL:

```sql
-- Add after the CREATE TABLE statement
CREATE INDEX IF NOT EXISTS ix_prescription_record_id
    ON prescription_schema.prescription ("recordId");

CREATE INDEX IF NOT EXISTS ix_prescription_drug_id
    ON prescription_schema.prescription ("drugId");
```

---

### FIX-29: Guard `Base.metadata.create_all()` behind environment check [MEDIUM]

**Files:**
- `drug_catalogue_service/app/__init__.py` line 35
- `prescription_service/app/__init__.py` line 57

**Problem:** Both services run `Base.metadata.create_all(bind=engine)` on every startup. In production with multiple workers, this causes race conditions on DDL. Should use Alembic migrations in production.

**Fix (minimum viable):** Guard behind environment check:

```python
import os

# Only create tables in local development
if os.getenv("APP_ENV", "local") != "docker":
    Base.metadata.create_all(bind=engine)
```

In Docker/production, tables should be created by `db/init.sql` which runs during `docker-compose up`.

---

## 5. Implementation Order

Execute fixes in this order to minimize conflicts and ensure each fix builds on the previous:

### Phase 1: Critical Fixes (do first — service may crash or corrupt data)

| Fix | Service | Effort | Description |
|-----|---------|--------|-------------|
| FIX-1 | Orchestrator | 1 min | Delete dead `db.py` |
| FIX-2 | Orchestrator | 1 min | Delete placeholder model/repository |
| FIX-19 | Prescription | 2 min | Fix `reload=True` in production |
| FIX-3 | Orchestrator | 5 min | Fix invoice payload mismatch |
| FIX-4 + FIX-15 | Drug Catalogue + Orchestrator | 30 min | Atomic stock deduction endpoint |

### Phase 2: Data Integrity (prevents orphaned/corrupt data)

| Fix | Service | Effort | Description |
|-----|---------|--------|-------------|
| FIX-5 | Orchestrator | 20 min | Prescription rollback on invoice failure |
| FIX-13 | Drug Catalogue | 10 min | Catch IntegrityError in add/update |
| FIX-20 | Prescription | 15 min | Remove dangerous `get_next_record_id()` |
| FIX-21 | Prescription | 5 min | Error handling on delete |

### Phase 3: Architectural Alignment (match make_payment patterns)

| Fix | Service | Effort | Description |
|-----|---------|--------|-------------|
| FIX-6 | Orchestrator | 45 min | Create client abstraction layer |
| FIX-8 | Orchestrator | 15 min | Register Flask error handlers |
| FIX-7 | Orchestrator | 2 min | Remove unused InvoiceStatus enum |
| FIX-9 | Orchestrator | 2 min | Remove unused schemas.py |

### Phase 4: Observability & Quality (production readiness)

| Fix | Service | Effort | Description |
|-----|---------|--------|-------------|
| FIX-10 | Orchestrator | 5 min | Health endpoint |
| FIX-16 | Drug Catalogue | 5 min | Health endpoint |
| FIX-24 | Prescription | 5 min | Health endpoint |
| FIX-11 | Orchestrator | 15 min | Add logging |
| FIX-17 | Drug Catalogue | 15 min | Add logging |
| FIX-25 | Prescription | 15 min | Add logging |
| FIX-12 | Orchestrator | 5 min | Remove unused exception classes |

### Phase 5: API Improvements (better developer experience)

| Fix | Service | Effort | Description |
|-----|---------|--------|-------------|
| FIX-14 | Drug Catalogue | 15 min | Pagination on list endpoint |
| FIX-22 | Prescription | 15 min | Pagination on list endpoint |
| FIX-23 | Prescription | 5 min | Remove duplicate validation |
| FIX-26 | Prescription | 15 min | Query prescriptions by record_id |
| FIX-18 | Drug Catalogue | 5 min | IntegrityError on delete |
| FIX-27 | Cross-service | 15 min | Standardize error format |
| FIX-28 | Prescription DB | 5 min | Add database indexes |
| FIX-29 | Both services | 5 min | Guard create_all() |

---

**Estimated Total Effort:** ~6 hours

**Phase 1-2 (Critical + Integrity):** ~1.5 hours — Must be done before any testing
**Phase 3 (Architecture):** ~1 hour — Significant refactor of orchestrator
**Phase 4 (Observability):** ~1 hour — Straightforward additions
**Phase 5 (API Improvements):** ~1.5 hours — Nice-to-have improvements
