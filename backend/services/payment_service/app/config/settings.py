import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")

if APP_ENV == "docker":
    DB_HOST = "postgres"  # compose service name — services share esd-net
else:
    DB_HOST = "localhost"

DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_SCHEMA = os.getenv("DB_SCHEMA", "payment_schema")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
INVOICE_SERVICE_URL = os.getenv("INVOICE_SERVICE_URL", "http://localhost:5003")
MAKE_PAYMENT_SERVICE_URL = os.getenv(
    "MAKE_PAYMENT_SERVICE_URL",
    os.getenv("make_payment_SERVICE_URL", "http://localhost:5008"),
)

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "changeme-dev-key")
