import os
import sys
import time as time_module
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

# Включаем режим тестирования (используется TEST_DATABASE_URL из .env)
os.environ["TESTING"] = "1"
test_db_url = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:admin@localhost:5432/postgre-test",
).strip()
os.environ["TEST_DATABASE_URL"] = test_db_url

import pytest
from fastapi.testclient import TestClient

from database.create_db import engine
from database.models import Base
from main import app
from src.services.selenium_service import get_active_sessions, stop_active_session


@pytest.fixture()
def db_setup():
    """Очищает и пересоздает таблицы в тестовой БД (TEST_DATABASE_URL) перед каждым интеграционным тестом."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    for sess in get_active_sessions():
        stop_active_session(str(sess["session_id"]))
    for _ in range(20):
        if not get_active_sessions():
            break
        time_module.sleep(0.1)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_setup):
    """Тестовый клиент FastAPI, подключенный к тестовой БД PostgreSQL (postgre-test)."""
    with TestClient(app) as test_client:
        yield test_client
