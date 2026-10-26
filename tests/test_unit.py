import sys
from pathlib import Path
from datetime import time as dt_time
from unittest.mock import MagicMock

# Позволяет запускать файл напрямую кнопкой Run Python File в VS Code
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from pydantic import ValidationError
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException

from src.models.regularactionmodel import RegularActionCreate
from src.services.selenium_service import (
    _xpath_literal,
    _normalize_cookies_list,
    find_element_sequentially_once,
    perform_step_action,
)


def test_unit_1_xpath_literal_escaping():
    """Unit-тест 1: Экранирование кавычек в строках при генерации XPath-выражений."""
    assert _xpath_literal("Войти") == "'Войти'"
    assert _xpath_literal("It's me") == '"It\'s me"'
    assert _xpath_literal("A 'quote' and \"double\"").startswith("concat(")


def test_unit_2_normalize_cookies_formats():
    """Unit-тест 2: Нормализация куки из списка объектов браузера и из словаря {key: value}."""
    raw_list = [
        {
            "name": "access",
            "value": "jwt_token",
            "domain": ".mts-link.ru",
            "path": "/",
            "secure": True,
            "httpOnly": False,
            "expirationDate": 1824533637,
            "hostOnly": False,
            "sameSite": "no_restriction",
        }
    ]
    res_list = _normalize_cookies_list(raw_list)
    assert res_list == [
        {
            "name": "access",
            "value": "jwt_token",
            "domain": ".mts-link.ru",
            "path": "/",
            "secure": True,
            "httpOnly": False,
        }
    ]

    raw_dict = {"_ga": "GA1.2.123"}
    res_dict = _normalize_cookies_list(raw_dict)
    assert res_dict == [{"name": "_ga", "value": "GA1.2.123", "path": "/"}]


def test_unit_3_sequential_locator_search_order():
    """Unit-тест 3: Последовательный поиск элемента по [текст, id, name, тэг, class, xpath]."""
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
        lambda by, val: [mock_el] if by == By.ID and val == "login-id" else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "login-id")
    assert el is mock_el
    assert strategy == "id"

    # 3. XPATH
    mock_driver.find_elements.side_effect = (
        lambda by, val: [mock_el]
        if by == By.XPATH and val == "//button[@id='x']"
        else []
    )
    el, strategy = find_element_sequentially_once(mock_driver, "//button[@id='x']")
    assert el is mock_el
    assert strategy == "xpath"


def test_unit_4_perform_step_action_click_and_input():
    """Unit-тест 4: Выполнение действий 'click' (с JS-fallback) и ввода текста (send_keys)."""
    mock_driver = MagicMock()
    mock_el = MagicMock()

    assert perform_step_action(mock_driver, mock_el, "click") == "click"
    mock_el.click.assert_called_once()

    # Fallback через execute_script при перекрытии кнопки
    mock_el.click.side_effect = ElementClickInterceptedException("intercepted")
    assert perform_step_action(mock_driver, mock_el, "click") == "click"
    mock_driver.execute_script.assert_any_call("arguments[0].click();", mock_el)

    # Ввод текста
    assert (
        perform_step_action(mock_driver, mock_el, "Тестовый ввод")
        == "send_keys('Тестовый ввод')"
    )
    mock_el.send_keys.assert_called_with("Тестовый ввод")


def test_unit_5_regular_action_day_validation():
    """Unit-тест 5: Валидация допустимого диапазона дня недели (0..6) в Pydantic-схеме."""
    valid_model = RegularActionCreate(
        instr_id=1,
        day=4,
        time_start=dt_time(10, 0),
        time_end=dt_time(11, 30),
    )
    assert valid_model.day == 4

    with pytest.raises(ValidationError):
        RegularActionCreate(
            instr_id=1,
            day=8,  # Ошибка: день недели должен быть от 0 до 6
            time_start=dt_time(10, 0),
            time_end=dt_time(11, 30),
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
