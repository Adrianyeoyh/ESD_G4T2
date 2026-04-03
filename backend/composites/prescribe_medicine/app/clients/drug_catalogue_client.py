from app.config import settings
from app.clients.base import http_request


def get_drug(drug_id: int) -> dict:
    """Fetch a single drug by ID."""
    url = f"{settings.DRUG_CATALOGUE_URL}/drug/{drug_id}"
    return http_request("GET", url)


def get_all_drugs() -> list[dict]:
    """Fetch all drugs from the catalogue."""
    url = f"{settings.DRUG_CATALOGUE_URL}/drug"
    return http_request("GET", url)


def deduct_stock(drug_id: int, amount: int) -> dict:
    """Atomically deduct stock. Returns updated drug or raises ConflictError if insufficient."""
    url = f"{settings.DRUG_CATALOGUE_URL}/drug/{drug_id}/deduct"
    return http_request("PATCH", url, {"amount": amount})


def restore_stock(drug_id: int, amount: int) -> dict:
    """Atomically restore stock (for rollback scenarios)."""
    url = f"{settings.DRUG_CATALOGUE_URL}/drug/{drug_id}/restore"
    return http_request("PATCH", url, {"amount": amount})
