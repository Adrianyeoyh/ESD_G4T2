import uvicorn
from fastapi import FastAPI
from sqlalchemy import text
from app.routes.drug_routes import router
from app.config.drug_db import Base, engine

# Ensure model metadata is registered before create_all runs.
from app.models.drug_model import Drug 

# Initialize FastAPI
app = FastAPI(
    title="Drug Catalogue Service",
    description="Atomic microservice for managing drug inventory"
)


def check_constraint_exists(conn, constraint_name: str) -> bool:
    """Check if a constraint already exists on the drug table"""
    try:
        result = conn.execute(text(f"""
            SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_schema = 'drug_schema' AND table_name = 'drug'
            AND constraint_name = '{constraint_name}'
        """))
        return result.fetchone() is not None
    except Exception:
        return False


def apply_migrations(conn) -> None:
    """Apply database schema migrations"""
    # Add unique constraint on drug_name if it doesn't exist
    if not check_constraint_exists(conn, "uq_drug_name"):
        try:
            conn.execute(text("""
                ALTER TABLE drug_schema.drug
                ADD CONSTRAINT uq_drug_name UNIQUE ("drugName")
            """))
        except Exception:
            pass
    
    # Add check constraint for quantity if it doesn't exist
    if not check_constraint_exists(conn, "ck_quantity_non_negative"):
        try:
            conn.execute(text("""
                ALTER TABLE drug_schema.drug
                ADD CONSTRAINT ck_quantity_non_negative CHECK (quantity >= 0)
            """))
        except Exception:
            pass
    
    # Add check constraint for price if it doesn't exist
    if not check_constraint_exists(conn, "ck_price_positive"):
        try:
            conn.execute(text("""
                ALTER TABLE drug_schema.drug
                ADD CONSTRAINT ck_price_positive CHECK (price > 0)
            """))
        except Exception:
            pass
    
    # Modify drug_name column to limit length to 255
    try:
        conn.execute(text("""
            ALTER TABLE drug_schema.drug
            ALTER COLUMN "drugName" TYPE VARCHAR(255)
        """))
    except Exception:
        pass


@app.on_event("startup")
def init_db() -> None:
    # Create schema first when using an external DB that may not be pre-initialized.
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS drug_schema"))
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Apply any pending migrations
    with engine.begin() as conn:
        apply_migrations(conn)


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)