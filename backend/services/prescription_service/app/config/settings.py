import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")

if APP_ENV == "docker":
    DB_HOST = "postgres"  # compose service name — services share esd-net
else:
    DB_HOST = "localhost"
    
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "clinic")
DB_PASSWORD = os.getenv("DB_PASSWORD", "clinic")
DB_NAME = os.getenv("DB_NAME", "esd_db")
DB_SCHEMA = os.getenv("DB_SCHEMA", "prescription_schema")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)