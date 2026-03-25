from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import DATABASE_URL, DB_SCHEMA

# Use service schema from settings.py.
engine = create_engine(
    DATABASE_URL,
    connect_args={"options": f"-csearch_path={DB_SCHEMA}"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()