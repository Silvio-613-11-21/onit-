import os
import time as time_module
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Используем тестовую БД для автотестов, не меняя .env с PostgreSQL
os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"

import pytest
from fastapi.testclient import TestClient
from selenium.webdriver.common.by import By

from ..database.create_db import engine
from ..database.models import Base
from main import app
from src.services.selenium_service import (
    find_element_sequentially_once,
    perform_step_action,
    execute_instruction_sync,
    get_active_sessions,
    stop_active_session,
)
from src.services.scheduler_service import SchedulerService


@pytest.fixture(autouse=True)
def setup_test_db():
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


def test_crud_normalized_steps_cookies_and_instructions():
    with TestClient(app) as client:
        # 1. Создание набора куки в таблице cookie (формат массива объектов Selenium)
        cookie_payload = {
            "title": "МТС Линк Основной",
            "cookie": [
                {
                    "name": "_ga",
                    "value": "GA1.2.118533033.1789973637",
                    "domain": ".mts-link.ru",
                    "path": "/",
                },
                {
                    "name": "access",
                    "value": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "domain": ".mts-link.ru",
                    "path": "/",
                },
            ],
        }
        resp_cookie = client.post("/cookies", json=cookie_payload)
        assert resp_cookie.status_code == 201
        cookie_record = resp_cookie.json()
        cookie_id = cookie_record["id"]
        assert cookie_record["title"] == "МТС Линк Основной"
        assert isinstance(cookie_record["cookie"], list)
        assert len(cookie_record["cookie"]) == 2
        assert "name" in cookie_record["cookie"][0]
        assert "domain" in cookie_record["cookie"][0]

        # 2. Создание шаблона шагов в таблице step
        step_payload = {
            "title": "Вход в вебинар МТС Линк",
            "steps": {
                "Войти": "click",
                "username": "Иван Иванов",
                "button.Button__btn___QAHvH.OdinControl__control___b1rRn": "click",
            },
        }
        resp_step = client.post("/steps", json=step_payload)
        assert resp_step.status_code == 201
        step_record = resp_step.json()
        step_id = step_record["id"]
        assert step_record["steps"] == step_payload["steps"]

        # 3. Создание ДВУХ разных инструкций с разными URL, но ОДНИМ И ТЕМ ЖЕ step_id и cookie_id (без дублирования)
        instr1_resp = client.post(
            "/create_instruction",
            json={
                "url": "https://my.mts-link.ru/j/120328607/111111",
                "step_id": step_id,
                "cookie_id": cookie_id,
            },
        )
        assert instr1_resp.status_code == 201
        instr1 = instr1_resp.json()
        instr1_id = instr1["id"]
        assert instr1["step_id"] == step_id
        assert instr1["cookie_id"] == cookie_id
        assert instr1["steps"] == step_payload["steps"]

        instr2_resp = client.post(
            "/instructions",
            json={
                "url": "https://my.mts-link.ru/j/120328607/222222",
                "step_id": step_id,
                "cookie_id": cookie_id,
            },
        )
        assert instr2_resp.status_code == 201
        instr2 = instr2_resp.json()
        instr2_id = instr2["id"]
        assert instr2["step_id"] == step_id
        assert instr2["cookie_id"] == cookie_id

        # 4. Обновление шаблона шагов автоматически отражается в обеих инструкциях
        new_steps = {"Подключиться": "click"}
        resp_step_upd = client.put(f"/steps/{step_id}", json={"steps": new_steps})
        assert resp_step_upd.status_code == 200

        instr1_after = client.get(f"/instructions/{instr1_id}").json()
        instr2_after = client.get(f"/instructions/{instr2_id}").json()
        assert instr1_after["steps"] == new_steps
        assert instr2_after["steps"] == new_steps

        # 5. Создание регулярной и нерегулярной инструкции
        reg_resp = client.post(
            "/regular_actions",
            json={
                "instr_id": instr1_id,
                "day": 1,
                "time_start": "09:00:00",
                "time_end": "10:30:00",
            },
        )
        assert reg_resp.status_code == 201
        reg_id = reg_resp.json()["id"]

        single_resp = client.post(
            "/single_actions",
            json={
                "instr_id": instr2_id,
                "date": "2026-10-13",
                "time_start": "12:00:00",
                "time_end": "13:30:00",
                "is_complete": False,
            },
        )
        assert single_resp.status_code == 201
        single_id = single_resp.json()["id"]

        # 6. Удаление расписаний, инструкций, шагов и куки
        assert client.delete(f"/regular_actions/{reg_id}").status_code == 200
        assert client.delete(f"/single_actions/{single_id}").status_code == 200
        assert client.delete(f"/instructions/{instr1_id}").status_code == 200
        assert client.delete(f"/instructions/{instr2_id}").status_code == 200
        assert client.delete(f"/steps/{step_id}").status_code == 200
        assert client.delete(f"/cookies/{cookie_id}").status_code == 200


def test_sequential_locator_search_all_strategies():
    """
    Проверяет, что поиск элемента идет строго последовательно по
    [текст, id, name, тэг, class, xpath] и находит 1-е сходство.
    """
    mock_driver = MagicMock()
    mock_el = MagicMock()
    mock_el.is_displayed.return_value = True

    # 1. Текст
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.LINK_TEXT and val == "Подключиться" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "Подключиться")
    assert el is mock_el
    assert strategy is not None and "текст" in strategy

    # 2. ID
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.ID and val == "submit-btn" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "submit-btn")
    assert el is mock_el
    assert strategy == "id"

    # 3. NAME
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.NAME and val == "email_field" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "email_field")
    assert el is mock_el
    assert strategy == "name"

    # 4. ТЭГ
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.TAG_NAME and val == "button" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "button")
    assert el is mock_el
    assert strategy == "тэг"

    # 5. CLASS
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.CLASS_NAME and val == "btn-primary" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "btn-primary")
    assert el is mock_el
    assert strategy is not None and "class" in strategy

    # 6. XPATH
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el]
        if by == By.XPATH and val == "//button[@data-test='join']"
        else []
    )
    el, strategy = find_element_sequentially_once(
        mock_driver, "//button[@data-test='join']"
    )
    assert el is mock_el
    assert strategy == "xpath"


def test_step_actions_click_and_input():
    mock_driver = MagicMock()
    mock_el = MagicMock()

    # Клик
    res_click = perform_step_action(mock_driver, mock_el, "click")
    assert res_click == "click"
    mock_el.click.assert_called_once()

    # Ввод текста
    res_input = perform_step_action(mock_driver, mock_el, "Привет мир")
    assert "send_keys" in res_input
    mock_el.send_keys.assert_called_with("Привет мир")


def test_execute_instruction_and_scheduler_matching():
    with TestClient(app) as client:
        now = datetime.now()
        start_t = (now - timedelta(minutes=1)).time().replace(microsecond=0)
        end_t = (now + timedelta(seconds=1)).time().replace(microsecond=0)

        # Создаем шаблон шагов и куки в отдельных таблицах
        step_resp = client.post(
            "/steps",
            json={
                "title": "Шаги входа",
                "steps": {"login_btn": "click", "user_input": "test_user"},
            },
        )
        step_id = step_resp.json()["id"]

        cookie_resp = client.post(
            "/cookies",
            json={
                "title": "Куки тестовые",
                "cookie": [
                    {
                        "name": "session_id",
                        "value": "abc123xyz",
                        "domain": ".example.com",
                        "path": "/",
                    }
                ],
            },
        )
        cookie_id = cookie_resp.json()["id"]

        instr_resp = client.post(
            "/instructions",
            json={
                "url": "https://example.com",
                "step_id": step_id,
                "cookie_id": cookie_id,
            },
        )
        instr_id = instr_resp.json()["id"]

        # 1. Нерегулярная инструкция на текущую дату и время
        single_resp = client.post(
            "/single_actions",
            json={
                "instr_id": instr_id,
                "date": now.date().isoformat(),
                "time_start": start_t.isoformat(),
                "time_end": end_t.isoformat(),
                "is_complete": False,
            },
        )
        single_id = single_resp.json()["id"]

        # 2. Регулярная инструкция на текущий день недели и время
        reg_resp = client.post(
            "/regular_actions",
            json={
                "instr_id": instr_id,
                "day": now.weekday(),
                "time_start": start_t.isoformat(),
                "time_end": end_t.isoformat(),
            },
        )
        reg_id = reg_resp.json()["id"]

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
                steps={"login_btn": "click", "user_input": "test_user"},
                cookie=[
                    {
                        "name": "session_id",
                        "value": "abc123xyz",
                        "domain": ".example.com",
                        "path": "/",
                    }
                ],
                time_end=end_t,
                source="test",
            )
            assert result["is_success"] is True
            assert result["cookies_added"] == 1
            mock_driver.get.assert_called_once_with("https://example.com")
            mock_driver.add_cookie.assert_called()
            mock_driver.refresh.assert_called_once()
            mock_driver.quit.assert_called_once()

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

            # Повторный тик в тот же день не должен запускать ту же регулярную инструкцию дважды
            check_res_second = scheduler.check_and_trigger_now()
            assert len(check_res_second["launched_regular_actions"]) == 0
            assert len(check_res_second["launched_single_actions"]) == 0

            # Дожидаемся завершения фоновых потоков
            for _ in range(30):
                if not get_active_sessions():
                    break
                time_module.sleep(0.1)

            logs = client.get(f"/logs?instr_id={instr_id}").json()
            assert len(logs) == 3
            assert all(log["is_success"] for log in logs)
