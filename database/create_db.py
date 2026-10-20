import os
import logging
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session

try:
    from database.models import Base
except ImportError:
    from models import Base

logger = logging.getLogger(__name__)

load_dotenv()

url = os.getenv("DATABASE_URL")

if not url:
    raise ValueError("Нет DATABASE_URL в env")

engine = create_engine(url, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

def init_db() -> None:
    inspector = inspect(engine)
    if inspector.has_table("instruction"):
        logger.info("БД уже существует")
        return 
    Base.metadata.create_all(bind=engine)
    logger.info("БД создано")

def rm_db() -> None:
    Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    init_db()

