import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")

DRUG_CATALOGUE_URL = os.getenv("DRUG_CATALOGUE_URL", "http://localhost:5001")
INVOICE_SERVICE_URL = os.getenv("INVOICE_SERVICE_URL", "http://localhost:5003")
PRESCRIPTION_SERVICE_URL = os.getenv("PRESCRIPTION_SERVICE_URL", "http://localhost:5005")
CLINICAL_RECORDS_URL = os.getenv("CLINICAL_RECORDS_URL", "http://localhost:5006")
CLINICAL_RECORD_VALIDATE_PATH = os.getenv(
	"CLINICAL_RECORD_VALIDATE_PATH",
	"/record/{record_id}",
)

CLINICAL_RECORDS_REQUIRED = os.getenv("CLINICAL_RECORDS_REQUIRED", "false").lower() == "true"
HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", 8))