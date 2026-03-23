import uvicorn
from fastapi import FastAPI
from sqlalchemy import text
from app.controllers.drug_controller import router
from app.config.drug_db import Base, engine

# Ensure model metadata is registered before create_all runs.
from app.models.drug_model import Drug  # noqa: F401

# Initialize FastAPI
app = FastAPI(
    title="Drug Catalogue Service",
    description="Atomic microservice for managing drug inventory"
)


@app.on_event("startup")
def init_db() -> None:
    # Create schema first when using an external DB that may not be pre-initialized.
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS drug_schema"))
    Base.metadata.create_all(bind=engine)


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)