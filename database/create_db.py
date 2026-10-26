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

if os.getenv("TESTING") == "1":
    url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://postgres:admin@localhost:5432/postgre-test",
    )
else:
    url = os.getenv("DATABASE_URL")

if not url:
    raise ValueError("Нет DATABASE_URL в env")

url = url.strip()
echo_sql = os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")

engine = create_engine(url, echo=echo_sql, pool_pre_ping=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def init_db() -> None:
    """
    Создает все таблицы в базе данных.
    Если в БД осталась старая схема таблицы instruction (без колонки step_id),
    автоматически пересоздает таблицы под новую нормализованную схему.
    """
    inspector = inspect(engine)
    if inspector.has_table("instruction"):
        col_names = {col["name"] for col in inspector.get_columns("instruction")}
        if "step_id" not in col_names:
            logger.info(
                "Обнаружена старая схема таблицы instruction (без step_id). Пересоздание таблиц..."
            )
            Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Генератор сессии БД для зависимостей FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Таблицы успешно созданы в БД.")
