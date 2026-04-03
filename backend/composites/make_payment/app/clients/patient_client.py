from app.clients.base import http_request
from app.config import settings


def get_patient(patient_id: str) -> dict:
    url = f"{settings.PATIENT_SERVICE_URL}/patient/{patient_id}"
    return http_request("GET", url)
