from fastapi import FastAPI
from pydantic import BaseModel


class PrescriptionCreate(BaseModel):
    record_id: int
    drug_id: int
    quantity: int
    notes: str | None = None


app = FastAPI(
    title="Prescription Service",
    version="1.0.0",
    description="Service for storing and retrieving prescriptions",
)

_prescriptions: list[dict] = []
_next_id = 1


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/prescriptions")
def list_prescriptions():
    return _prescriptions


@app.post("/prescriptions", status_code=201)
def create_prescription(payload: PrescriptionCreate):
    global _next_id
    row = {
        "prescriptionId": _next_id,
        "recordId": payload.record_id,
        "drugId": payload.drug_id,
        "quantity": payload.quantity,
        "notes": payload.notes,
    }
    _next_id += 1
    _prescriptions.append(row)
    return row
