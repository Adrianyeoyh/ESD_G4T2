import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")

if APP_ENV == "docker":
    INVOICE_SERVICE_URL = os.getenv("INVOICE_SERVICE_URL", "http://invoice_service:5003")
    PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:5004")
    RECORDS_SERVICE_URL = os.getenv("RECORDS_SERVICE_URL", "http://records_service:5006")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
else:
    INVOICE_SERVICE_URL = os.getenv("INVOICE_SERVICE_URL", "http://localhost:5003")
    PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:5004")
    RECORDS_SERVICE_URL = os.getenv("RECORDS_SERVICE_URL", "http://localhost:5006")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "8"))
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "sgd")
NOTIFICATION_PHONE_NUMBER = os.getenv("NOTIFICATION_PHONE_NUMBER", "+6588888888")

RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "notification.payment.success")

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "changeme-dev-key")
