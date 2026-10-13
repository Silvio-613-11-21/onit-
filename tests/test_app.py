import os
import time as time_module
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Используем тестовую БД для автотестов, не меняя .env с PostgreSQL
os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"

import pytest
from fastapi.testclient import TestClient
from selenium.webdriver.common.by import By

from database.create_db import engine
from database.models import Base
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
        stop_active_session(sess["session_id"])
    for _ in range(20):
        if not get_active_sessions():
            break
        time_module.sleep(0.1)
    Base.metadata.drop_all(bind=engine)


def test_crud_and_cookie_parsing():
    with TestClient(app) as client:
        # 1. Парсинг cookie.txt
        resp_cookies = client.get("/cookies/from-file")
        assert resp_cookies.status_code == 200
        cookies_dict = resp_cookies.json()
        assert "_ga" in cookies_dict
        assert "access" in cookies_dict

        # 2. Создание инструкции
        instr_payload = {
            "url": "https://my.mts-link.ru/j/120328607/24334684457",
            "steps": {
                "Войти": "click",
                "username": "Иван Иванов",
                "button.Button__btn___QAHvH.OdinControl__control___b1rRn": "click",
            },
            "cookie": {"_ga": cookies_dict["_ga"], "access": cookies_dict["access"]},
        }
        resp = client.post("/create_instruction", json=instr_payload)
        assert resp.status_code == 201
        instr = resp.json()
        instr_id = instr["id"]
        assert instr["url"] == instr_payload["url"]
        assert instr["steps"] == instr_payload["steps"]
        assert instr["cookie"]["_ga"] == cookies_dict["_ga"]

        # 3. Обновление инструкции
        resp_upd = client.put(
            f"/instructions/{instr_id}",
            json={"url": "https://my.mts-link.ru/j/999"},
        )
        assert resp_upd.status_code == 200
        assert resp_upd.json()["url"] == "https://my.mts-link.ru/j/999"

        # 4. Получение всех инструкций
        resp_list = client.get("/instructions")
        assert resp_list.status_code == 200
        assert len(resp_list.json()) == 1

        # 5. Создание и обновление регулярной инструкции
        reg_payload = {
            "instr_id": instr_id,
            "day": 1,
            "time_start": "09:00:00",
            "time_end": "10:30:00",
        }
        resp_reg = client.post("/regular_actions", json=reg_payload)
        assert resp_reg.status_code == 201
        reg_id = resp_reg.json()["id"]

        resp_reg_upd = client.put(f"/regular_actions/{reg_id}", json={"day": 2})
        assert resp_reg_upd.status_code == 200
        assert resp_reg_upd.json()["day"] == 2

        # 6. Создание и обновление нерегулярной инструкции
        single_payload = {
            "instr_id": instr_id,
            "date": "2026-10-13",
            "time_start": "12:00:00",
            "time_end": "13:30:00",
            "is_complete": False,
        }
        resp_single = client.post("/single_actions", json=single_payload)
        assert resp_single.status_code == 201
        single_id = resp_single.json()["id"]

        resp_single_upd = client.put(
            f"/single_actions/{single_id}", json={"is_complete": True}
        )
        assert resp_single_upd.status_code == 200
        assert resp_single_upd.json()["is_complete"] is True

        # 7. Создание и получение лога
        log_payload = {
            "instr_id": instr_id,
            "is_success": True,
            "message": "Тестовый лог",
        }
        resp_log = client.post("/logs", json=log_payload)
        assert resp_log.status_code == 201
        assert resp_log.json()["message"] == "Тестовый лог"

        # 8. Удаление расписаний и инструкции
        assert client.delete(f"/regular_actions/{reg_id}").status_code == 200
        assert client.delete(f"/single_actions/{single_id}").status_code == 200
        assert client.delete(f"/instructions/{instr_id}").status_code == 200


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
    assert el is mock_el and "текст" in strategy

    # 2. ID
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.ID and val == "submit-btn" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "submit-btn")
    assert el is mock_el and strategy == "id"

    # 3. NAME
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.NAME and val == "email_field" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "email_field")
    assert el is mock_el and strategy == "name"

    # 4. ТЭГ
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.TAG_NAME and val == "button" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "button")
    assert el is mock_el and strategy == "тэг"

    # 5. CLASS
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el] if by == By.CLASS_NAME and val == "btn-primary" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "btn-primary")
    assert el is mock_el and "class" in strategy

    # 6. XPATH
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el]
        if by == By.XPATH and val == "//button[@data-test='join']"
        else []
    )
    el, strategy = find_element_sequentially_once(
        mock_driver, "//button[@data-test='join']"
    )
    assert el is mock_el and strategy == "xpath"


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

        instr_resp = client.post(
            "/instructions",
            json={
                "url": "https://example.com",
                "steps": {"login_btn": "click", "user_input": "test_user"},
                "cookie": {"session_id": "abc123xyz"},
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
                cookie={"session_id": "abc123xyz"},
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
            assert len(logs) == 3  # 1 прямой запуск + 1 single_action + 1 regular_action
            assert all(log["is_success"] for log in logs)
