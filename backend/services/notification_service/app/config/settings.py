import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")

if APP_ENV == "docker":
    RABBITMQ_HOST = "rabbitmq"
else:
    RABBITMQ_HOST = "localhost"

RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "notification.payment.success")

HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8081"))

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")