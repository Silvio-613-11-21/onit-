import os
import sys
import time as time_module
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Позволяет запускать файл напрямую кнопкой Run Python File в VS Code
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")
os.environ["TESTING"] = "1"

import pytest
from src.services.selenium_service import execute_instruction_sync, get_active_sessions
from src.services.scheduler_service import SchedulerService


def test_integration_1_normalized_steps_cookies_and_instructions(client):
    """
    Integration-тест 1: Создание записей в таблицах step, cookie и instruction в PostgreSQL
    (postgre-test) и проверка переиспользования одного набора шагов и куки для разных URL.
    """
    cookie_resp = client.post(
        "/cookies",
        json={
            "title": "МТС Линк Основной",
            "cookie": [
                {
                    "name": "access",
                    "value": "eyJhbG...",
                    "domain": ".mts-link.ru",
                    "path": "/",
                }
            ],
        },
    )
    assert cookie_resp.status_code == 201
    cookie_id = cookie_resp.json()["id"]

    step_resp = client.post(
        "/steps",
        json={
            "title": "Вход на вебинар",
            "steps": {"Войти": "click", "username": "Иван Иванов"},
        },
    )
    assert step_resp.status_code == 201
    step_id = step_resp.json()["id"]

    # Две инструкции с разными URL ссылаются на один и тот же step_id и cookie_id
    i1 = client.post(
        "/instructions",
        json={
            "url": "https://my.mts-link.ru/j/123/111",
            "step_id": step_id,
            "cookie_id": cookie_id,
        },
    )
    i2 = client.post(
        "/instructions",
        json={
            "url": "https://my.mts-link.ru/j/123/222",
            "step_id": step_id,
            "cookie_id": cookie_id,
        },
    )
    assert i1.status_code == 201 and i2.status_code == 201
    id1, id2 = i1.json()["id"], i2.json()["id"]

    # Обновление шагов в таблице step автоматически меняет steps в обеих инструкциях
    new_steps = {"Подключиться": "click"}
    client.put(f"/steps/{step_id}", json={"steps": new_steps})

    assert client.get(f"/instructions/{id1}").json()["steps"] == new_steps
    assert client.get(f"/instructions/{id2}").json()["steps"] == new_steps


def test_integration_2_selenium_execution_and_postgres_logging(client):
    """
    Integration-тест 2: Полный цикл выполнения инструкции (открытие URL, добавление куки,
    выполнение шагов) и проверка записи результата в таблицу log в PostgreSQL.
    """
    step_id = client.post(
        "/steps",
        json={"title": "Логин", "steps": {"login_btn": "click", "user_field": "admin"}},
    ).json()["id"]

    instr_id = client.post(
        "/instructions",
        json={"url": "https://example.com", "step_id": step_id, "cookie_id": None},
    ).json()["id"]

    mock_driver = MagicMock()
    mock_el = MagicMock()
    mock_el.is_displayed.return_value = True
    mock_driver.find_elements.return_value = [mock_el]

    with patch(
        "src.services.selenium_service.create_chrome_driver",
        return_value=mock_driver,
    ), patch("src.services.selenium_service.time_module.sleep"):
        result = execute_instruction_sync(
            instr_id=instr_id,
            url="https://example.com",
            steps={"login_btn": "click", "user_field": "admin"},
            cookie=[
                {
                    "name": "session",
                    "value": "123",
                    "domain": ".example.com",
                    "path": "/",
                }
            ],
            source="integration_test",
        )
        assert result["is_success"] is True
        assert result["cookies_added"] == 1
        mock_driver.get.assert_called_once_with("https://example.com")
        mock_driver.refresh.assert_called_once()
        mock_driver.quit.assert_called_once()

    logs = client.get(f"/logs?instr_id={instr_id}").json()
    assert len(logs) == 1
    assert logs[0]["is_success"] is True
    assert "Открыт URL: https://example.com" in logs[0]["message"]


def test_integration_3_scheduler_matches_db_time_with_system_time(client):
    """
    Integration-тест 3: Сверка системного времени с таблицами regular_action и single_action
    в PostgreSQL, автоматический запуск инструкций и выставление is_complete = True.
    """
    now = datetime.now()
    start_t = (now - timedelta(minutes=1)).time().replace(microsecond=0)
    end_t = (now + timedelta(seconds=1)).time().replace(microsecond=0)

    step_id = client.post(
        "/steps", json={"title": "Пара", "steps": {"join_btn": "click"}}
    ).json()["id"]
    instr_id = client.post(
        "/instructions",
        json={"url": "https://example.com", "step_id": step_id},
    ).json()["id"]

    single_id = client.post(
        "/single_actions",
        json={
            "instr_id": instr_id,
            "date": now.date().isoformat(),
            "time_start": start_t.isoformat(),
            "time_end": end_t.isoformat(),
            "is_complete": False,
        },
    ).json()["id"]

    reg_id = client.post(
        "/regular_actions",
        json={
            "instr_id": instr_id,
            "day": now.weekday(),
            "time_start": start_t.isoformat(),
            "time_end": end_t.isoformat(),
        },
    ).json()["id"]

    mock_driver = MagicMock()
    mock_el = MagicMock()
    mock_el.is_displayed.return_value = True
    mock_driver.find_elements.return_value = [mock_el]

    with patch(
        "src.services.selenium_service.create_chrome_driver",
        return_value=mock_driver,
    ), patch("src.services.selenium_service.time_module.sleep"):
        scheduler = SchedulerService(check_interval=10)
        check_res = scheduler.check_and_trigger_now()

        assert len(check_res["launched_single_actions"]) == 1
        assert (
            check_res["launched_single_actions"][0]["single_action_id"] == single_id
        )
        assert len(check_res["launched_regular_actions"]) == 1
        assert (
            check_res["launched_regular_actions"][0]["regular_action_id"] == reg_id
        )

        # Проверяем, что single_action отмечен выполненным в PostgreSQL
        updated_single = client.get(f"/single_actions/{single_id}").json()
        assert updated_single["is_complete"] is True

        for _ in range(30):
            if not get_active_sessions():
                break
            time_module.sleep(0.1)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
