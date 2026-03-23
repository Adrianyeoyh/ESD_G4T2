from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.config.db import get_db
from app.schemas.invoice_schema import InvoiceCreate, InvoiceUpdateTotal, InvoiceResponse
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoice", tags=["Invoice"])


# ── Service dependency ──────────────────────────────────────────────────────
def get_invoice_service(db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(db)


# ── Routes ──────────────────────────────────────────────────────────────────

@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(body: InvoiceCreate, svc: InvoiceService = Depends(get_invoice_service)):
    invoice = svc.create_invoice(record_id=body.record_id, total=body.total)
    return InvoiceResponse.model_validate(invoice)


@router.get("", response_model=list[InvoiceResponse])
def list_invoices(svc: InvoiceService = Depends(get_invoice_service)):
    return [InvoiceResponse.model_validate(i) for i in svc.list_invoices()]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, svc: InvoiceService = Depends(get_invoice_service)):
    return InvoiceResponse.model_validate(svc.get_invoice(invoice_id))


@router.get("/record/{record_id}", response_model=InvoiceResponse)
def get_invoice_by_record(record_id: int, svc: InvoiceService = Depends(get_invoice_service)):
    return InvoiceResponse.model_validate(svc.get_invoice_by_record_id(record_id))


@router.put("/{invoice_id}/total", response_model=InvoiceResponse)
def update_total(invoice_id: int, body: InvoiceUpdateTotal, svc: InvoiceService = Depends(get_invoice_service)):
    return InvoiceResponse.model_validate(svc.update_total(invoice_id, body.total))


@router.put("/{invoice_id}/payment-pending", response_model=InvoiceResponse)
def mark_payment_pending(invoice_id: int, svc: InvoiceService = Depends(get_invoice_service)):
    return InvoiceResponse.model_validate(svc.mark_payment_pending(invoice_id))


@router.put("/{invoice_id}/paid", response_model=InvoiceResponse)
def mark_paid(invoice_id: int, svc: InvoiceService = Depends(get_invoice_service)):
    return InvoiceResponse.model_validate(svc.mark_paid(invoice_id))


@router.put("/{invoice_id}/failed", response_model=InvoiceResponse)
def mark_failed(invoice_id: int, svc: InvoiceService = Depends(get_invoice_service)):
    return InvoiceResponse.model_validate(svc.mark_failed(invoice_id))


@router.put("/{invoice_id}/cancelled", response_model=InvoiceResponse)
def mark_cancelled(invoice_id: int, svc: InvoiceService = Depends(get_invoice_service)):
    return InvoiceResponse.model_validate(svc.mark_cancelled(invoice_id))


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, svc: InvoiceService = Depends(get_invoice_service)):
    svc.delete_invoice(invoice_id)
