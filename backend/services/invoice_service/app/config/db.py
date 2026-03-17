from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import DATABASE_URL



engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-csearch_path=invoice_schema"}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()