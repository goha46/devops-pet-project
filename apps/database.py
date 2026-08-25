import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app_user:app_pass@db:5432/app_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
