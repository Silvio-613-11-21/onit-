import os
import time as time_module
import uuid
import threading
import logging
from datetime import datetime, time as dt_time
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    WebDriverException,
    InvalidSelectorException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)

from src.models.logmodel import LogCreate
from src.repositories.logrep import create_log, update_log_message

logger = logging.getLogger(__name__)

CookieDataInput = Union[List[Dict[str, Any]], Dict[str, Any]]

# Реестр активных сессий браузера (для мониторинга и управления через Swagger UI)
_active_sessions_lock = threading.Lock()
_active_sessions: Dict[str, Dict[str, Any]] = {}


def get_active_sessions() -> List[Dict[str, Any]]:
    """Возвращает список текущих активных сессий Selenium."""
    with _active_sessions_lock:
        result = []
        for sid, info in _active_sessions.items():
            item = {k: v for k, v in info.items() if k != "stop_event"}
            result.append(item)
        return result


def stop_active_session(session_id: str) -> bool:
    """Сигнализирует активной сессии Selenium досрочно закрыть браузер."""
    with _active_sessions_lock:
        info = _active_sessions.get(session_id)
        if not info:
            return False
        stop_event: threading.Event = info["stop_event"]
        stop_event.set()
        info["status"] = "stopping"
        return True


def is_instruction_currently_running(instr_id: int, source: Optional[str] = None) -> bool:
    """Проверяет, выполняется ли сейчас данная инструкция (или расписание)."""
    with _active_sessions_lock:
        for info in _active_sessions.values():
            if source and info.get("source") == source:
                return True
            if not source and info.get("instr_id") == instr_id:
                return True
        return False


def _xpath_literal(value: str) -> str:
    """Безопасное экранирование строки для XPath выражений."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    concat_parts = ", \"'\", ".join(f"'{p}'" for p in parts)
    return f"concat({concat_parts})"


def _pick_best_element(
    elements: List[WebElement], require_displayed: bool = False
) -> Optional[WebElement]:
    """Выбирает первый видимый элемент из списка найденных (или первый, если видимость не обязательна)."""
    if not elements:
        return None
    for el in elements:
        try:
            if el.is_displayed():
                return el
        except StaleElementReferenceException:
            continue
        except WebDriverException:
            continue
    if require_displayed:
        return None
    return elements[0]


def find_element_sequentially_once(
    driver: webdriver.Remote, selector: str
) -> Tuple[Optional[WebElement], Optional[str]]:
    """
    Последовательно проверяет локаторы в порядке:
    [текст, id, name, тэг, class, xpath]
    и возвращает первое совпадение (элемент, название_стратегии).
    """
    key = selector.strip()
    if not key:
        return None, None

    # 1. ТЕКСТ (точный текст ссылки, точный текст элемента, частичный текст элемента, частичный текст ссылки)
    try:
        els = driver.find_elements(By.LINK_TEXT, key)
        el = _pick_best_element(els, require_displayed=True)
        if el is not None:
            return el, "текст (LINK_TEXT)"

        escaped = _xpath_literal(key)
        non_meta = (
            "not(self::script) and not(self::style) and not(self::noscript) "
            "and not(self::title) and not(self::head) and not(self::meta) and not(self::link)"
        )
        exact_text_xpath = f"//*[{non_meta} and normalize-space(text()) = {escaped}]"
        els = driver.find_elements(By.XPATH, exact_text_xpath)
        el = _pick_best_element(els, require_displayed=True)
        if el is not None:
            return el, "текст (точное совпадение)"

        if not key.startswith(("/", "./", "(//")):
            partial_text_xpath = (
                f"//*[{non_meta} and contains(normalize-space(text()), {escaped})]"
            )
            els = driver.find_elements(By.XPATH, partial_text_xpath)
            el = _pick_best_element(els, require_displayed=True)
            if el is not None:
                return el, "текст (частичное совпадение)"

            els = driver.find_elements(By.PARTIAL_LINK_TEXT, key)
            el = _pick_best_element(els, require_displayed=True)
            if el is not None:
                return el, "текст (PARTIAL_LINK_TEXT)"
    except WebDriverException:
        pass

    # 2. ID (By.ID)
    try:
        els = driver.find_elements(By.ID, key)
        el = _pick_best_element(els)
        if el is not None:
            return el, "id"
    except WebDriverException:
        pass

    # 3. NAME (By.NAME)
    try:
        els = driver.find_elements(By.NAME, key)
        el = _pick_best_element(els)
        if el is not None:
            return el, "name"
    except WebDriverException:
        pass

    # 4. ТЭГ (By.TAG_NAME)
    try:
        if " " not in key and "/" not in key and "." not in key and "[" not in key:
            els = driver.find_elements(By.TAG_NAME, key)
            el = _pick_best_element(els)
            if el is not None:
                return el, "тэг"
    except WebDriverException:
        pass

    # 5. CLASS (By.CLASS_NAME и составные классы / CSS-селекторы классов)
    try:
        if " " not in key and "." not in key and "/" not in key:
            els = driver.find_elements(By.CLASS_NAME, key)
            el = _pick_best_element(els)
            if el is not None:
                return el, "class"
        elif " " in key and not key.startswith("/"):
            parts = [p.lstrip(".") for p in key.split() if p.strip()]
            if parts and all(
                p.replace("-", "").replace("_", "").isalnum() for p in parts
            ):
                css_cls = "." + ".".join(parts)
                els = driver.find_elements(By.CSS_SELECTOR, css_cls)
                el = _pick_best_element(els)
                if el is not None:
                    return el, "class (составной)"
        if "." in key and not key.startswith("/"):
            els = driver.find_elements(By.CSS_SELECTOR, key)
            el = _pick_best_element(els)
            if el is not None:
                return el, "class (CSS)"
    except (InvalidSelectorException, WebDriverException):
        pass

    # 6. XPATH (By.XPATH)
    try:
        els = driver.find_elements(By.XPATH, key)
        el = _pick_best_element(els)
        if el is not None:
            return el, "xpath"
    except (InvalidSelectorException, WebDriverException):
        pass

    return None, None


def find_first_matching_element(
    driver: webdriver.Remote, selector: str, timeout: float = 15.0
) -> Tuple[WebElement, str]:
    """
    Ожидает появления элемента до `timeout` секунд, на каждой итерации
    последовательно проверяя [текст, id, name, тэг, class, xpath].
    """
    deadline = time_module.monotonic() + max(timeout, 0.5)
    while True:
        element, strategy = find_element_sequentially_once(driver, selector)
        if element is not None and strategy is not None:
            return element, strategy

        if time_module.monotonic() >= deadline:
            break
        time_module.sleep(0.5)

    raise LookupError(
        f"Элемент по ключу '{selector}' не найден ни по одной из стратегий "
        f"[текст, id, name, тэг, class, xpath] за {timeout} сек."
    )


def perform_step_action(
    driver: webdriver.Remote, element: WebElement, action: Any
) -> str:
    """
    Выполняет действие над найденным элементом.
    - "click": клик по элементу
    - "double_click" / "dblclick": двойной клик
    - "clear": очистка поля ввода
    - "submit" / "enter": отправка / нажатие Enter
    - "hover": наведение курсора
    - "wait:N" / "sleep:N": пауза N секунд
    - любая другая строка (или "input:текст" / "send_keys:текст"): ввод текста в элемент
    """
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )
    except WebDriverException:
        pass

    action_str = str(action).strip()
    action_lower = action_str.lower()

    if action_lower == "click":
        try:
            element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script("arguments[0].click();", element)
        return "click"

    if action_lower in ("double_click", "dblclick"):
        ActionChains(driver).double_click(element).perform()
        return "double_click"

    if action_lower == "clear":
        element.clear()
        return "clear"

    if action_lower in ("submit", "enter"):
        element.send_keys(Keys.RETURN)
        return "enter"

    if action_lower in ("hover", "move_to"):
        ActionChains(driver).move_to_element(element).perform()
        return "hover"

    if action_lower.startswith(("wait:", "sleep:")):
        sec_str = action_str.split(":", 1)[1].strip()
        seconds = float(sec_str) if sec_str else 1.0
        time_module.sleep(seconds)
        return f"wait({seconds}s)"

    # Ввод текста (send_keys)
    if action_lower.startswith("input:"):
        text_to_send = action_str[6:]
    elif action_lower.startswith("send_keys:"):
        text_to_send = action_str[10:]
    else:
        text_to_send = action_str

    try:
        element.clear()
    except WebDriverException:
        pass
    element.send_keys(text_to_send)
    return f"send_keys('{text_to_send}')"


def _normalize_cookies_list(cookies: CookieDataInput) -> List[Dict[str, Any]]:
    """
    Приводит куки из БД (либо список объектов [{'name', 'value', 'domain', 'path'}],
    либо словарь {'name': 'value'}) к единому списку словарей для driver.add_cookie().
    """
    normalized: List[Dict[str, Any]] = []
    if isinstance(cookies, list):
        for item in cookies:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            value = item.get("value")
            if not name or value is None:
                continue
            cookie_dict: Dict[str, Any] = {
                "name": str(name),
                "value": str(value),
                "path": str(item.get("path") or "/"),
            }
            if item.get("domain"):
                cookie_dict["domain"] = str(item["domain"])
            if "secure" in item and isinstance(item["secure"], bool):
                cookie_dict["secure"] = item["secure"]
            if "httpOnly" in item and isinstance(item["httpOnly"], bool):
                cookie_dict["httpOnly"] = item["httpOnly"]
            normalized.append(cookie_dict)
    elif isinstance(cookies, dict):
        for name, val in cookies.items():
            if val is None:
                continue
            if isinstance(val, dict):
                cookie_dict = {
                    "name": str(name),
                    "value": str(val.get("value", "")),
                    "path": str(val.get("path") or "/"),
                }
                if val.get("domain"):
                    cookie_dict["domain"] = str(val["domain"])
            else:
                cookie_dict = {
                    "name": str(name),
                    "value": str(val),
                    "path": "/",
                }
            normalized.append(cookie_dict)
    return normalized


def add_cookies_to_driver(
    driver: webdriver.Remote, url: str, cookies: Optional[CookieDataInput]
) -> int:
    """
    Добавляет куки (из массива объектов Selenium или словаря {ключ: значение})
    в открытый браузер Selenium и обновляет страницу.
    Возвращает количество успешно добавленных куки.
    """
    if not cookies:
        return 0

    cookie_items = _normalize_cookies_list(cookies)
    if not cookie_items:
        return 0

    added_count = 0
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    parent_domain = None
    host_parts = hostname.split(".")
    if len(host_parts) >= 2:
        parent_domain = "." + ".".join(host_parts[-2:])

    for cookie_dict in cookie_items:
        name = cookie_dict.get("name", "")
        try:
            driver.add_cookie(cookie_dict)
            added_count += 1
            if (
                parent_domain
                and "domain" not in cookie_dict
                and len(host_parts) > 2
            ):
                try:
                    driver.add_cookie({**cookie_dict, "domain": parent_domain})
                except WebDriverException:
                    pass
        except WebDriverException as exc:
            if "domain" in cookie_dict:
                fallback_cookie = {
                    k: v for k, v in cookie_dict.items() if k != "domain"
                }
                try:
                    driver.add_cookie(fallback_cookie)
                    added_count += 1
                except WebDriverException:
                    logger.warning("Не удалось добавить куку %s: %s", name, exc)
            else:
                logger.warning("Не удалось добавить куку %s: %s", name, exc)

    if added_count > 0:
        driver.refresh()
        time_module.sleep(2.0)

    return added_count


def create_chrome_driver() -> webdriver.Chrome:
    """Создает и настраивает экземпляр Chrome WebDriver."""
    options = ChromeOptions()
    headless = os.getenv("SELENIUM_HEADLESS", "false").lower() in ("1", "true", "yes")
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.notifications": 1,
        },
    )
    return webdriver.Chrome(options=options)


def parse_cookie_file_to_selenium_list(content: str) -> List[Dict[str, str]]:
    """
    Парсит содержимое файла cookie.txt (разделенного табуляцией, как в s.py)
    в список объектов Selenium [{'name', 'value', 'domain', 'path'}].
    """
    result: List[Dict[str, str]] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split("\t")
        if len(parts) >= 4:
            name = parts[0].strip()
            value = parts[1].strip()
            domain = parts[2].strip()
            path = parts[3].strip() or "/"
            if name:
                result.append(
                    {
                        "name": name,
                        "value": value,
                        "domain": domain,
                        "path": path,
                    }
                )
        elif len(parts) >= 2:
            name = parts[0].strip()
            value = parts[1].strip()
            if name:
                result.append(
                    {
                        "name": name,
                        "value": value,
                        "path": "/",
                    }
                )
    return result


def parse_cookie_file_content(content: str) -> Dict[str, str]:
    """
    Парсит содержимое файла формата cookie.txt в простой словарь {name: value}.
    """
    result: Dict[str, str] = {}
    for item in parse_cookie_file_to_selenium_list(content):
        result[item["name"]] = item["value"]
    return result


def execute_instruction_sync(
    instr_id: int,
    url: str,
    steps: Dict[str, Any],
    cookie: Optional[CookieDataInput] = None,
    time_end: Optional[dt_time] = None,
    hold_seconds: int = 0,
    source: str = "manual",
) -> Dict[str, Any]:
    """
    Полный цикл выполнения инструкции через Selenium:
    1. Открывает ссылку `url`.
    2. Добавляет куки из БД (если они есть) и обновляет страницу.
    3. Последовательно выполняет все шаги из JSON `steps`, ища элементы
       по [текст, id, name, тэг, class, xpath].
    4. Если задано `time_end` (или `hold_seconds`), держит браузер открытым до `time_end`.
    5. Записывает результат в таблицу `log`.
    """
    session_id = str(uuid.uuid4())[:8]
    stop_event = threading.Event()
    started_at = datetime.now()

    with _active_sessions_lock:
        _active_sessions[session_id] = {
            "session_id": session_id,
            "instr_id": instr_id,
            "url": url,
            "source": source,
            "started_at": started_at.isoformat(timespec="seconds"),
            "time_end": time_end.isoformat() if time_end else None,
            "status": "starting",
            "stop_event": stop_event,
        }

    driver: Optional[webdriver.Remote] = None
    log_record_id: Optional[int] = None
    step_timeout = float(os.getenv("SELENIUM_STEP_TIMEOUT", "15"))

    try:
        driver = create_chrome_driver()

        with _active_sessions_lock:
            if session_id in _active_sessions:
                _active_sessions[session_id]["status"] = "opening_url"

        driver.get(url)
        time_module.sleep(2.0)

        # Добавление куки, если они есть в БД
        cookies_added = 0
        if cookie:
            with _active_sessions_lock:
                if session_id in _active_sessions:
                    _active_sessions[session_id]["status"] = "adding_cookies"
            cookies_added = add_cookies_to_driver(driver, url, cookie)

        # Выполнение шагов инструкции
        executed_steps: List[str] = []
        if steps and isinstance(steps, dict):
            with _active_sessions_lock:
                if session_id in _active_sessions:
                    _active_sessions[session_id]["status"] = "executing_steps"

            for selector_key, action_val in steps.items():
                if stop_event.is_set():
                    break

                if selector_key.strip().lower() in ("wait", "sleep", "pause"):
                    try:
                        pause_sec = float(action_val)
                    except (TypeError, ValueError):
                        pause_sec = 2.0
                    time_module.sleep(pause_sec)
                    executed_steps.append(f"пауза {pause_sec} сек.")
                    continue

                element, matched_by = find_first_matching_element(
                    driver, selector_key, timeout=step_timeout
                )
                performed = perform_step_action(driver, element, action_val)
                executed_steps.append(
                    f"'{selector_key}' (найден по: {matched_by}) -> {performed}"
                )
                time_module.sleep(1.0)

        steps_summary = "; ".join(executed_steps) if executed_steps else "без шагов"
        base_msg = (
            f"[{source}] Открыт URL: {url}. Куки добавлено: {cookies_added}. "
            f"Шаги выполнены ({len(executed_steps)}): {steps_summary}."
        )

        holding_msg = base_msg
        if time_end and datetime.now().time() < time_end:
            holding_msg = f"{base_msg} Браузер удерживается открытым до {time_end}."
        elif hold_seconds > 0:
            holding_msg = (
                f"{base_msg} Браузер удерживается открытым на {hold_seconds} сек."
            )

        db_log = create_log(
            LogCreate(
                instr_id=instr_id,
                is_success=True,
                message=holding_msg,
            )
        )
        log_record_id = db_log.id

        # Удержание браузера открытым до time_end или в течение hold_seconds
        if time_end is not None:
            with _active_sessions_lock:
                if session_id in _active_sessions:
                    _active_sessions[session_id]["status"] = f"holding_until_{time_end}"

            while not stop_event.is_set():
                now_time = datetime.now().time()
                if now_time >= time_end:
                    break
                stop_event.wait(timeout=1.0)

            closed_at = datetime.now().time().replace(microsecond=0)
            final_msg = f"{base_msg} Браузер закрыт в {closed_at} (плановое окончание: {time_end})."
            if log_record_id is not None:
                update_log_message(log_record_id, final_msg, is_success=True)

        elif hold_seconds > 0:
            with _active_sessions_lock:
                if session_id in _active_sessions:
                    _active_sessions[session_id]["status"] = f"holding_{hold_seconds}s"

            stop_event.wait(timeout=float(hold_seconds))
            closed_at = datetime.now().time().replace(microsecond=0)
            final_msg = f"{base_msg} Браузер закрыт в {closed_at} после удержания {hold_seconds} сек."
            if log_record_id is not None:
                update_log_message(log_record_id, final_msg, is_success=True)
        else:
            final_msg = base_msg

        return {
            "session_id": session_id,
            "instr_id": instr_id,
            "is_success": True,
            "cookies_added": cookies_added,
            "executed_steps": executed_steps,
            "log_id": log_record_id,
            "message": final_msg,
        }

    except Exception as exc:
        err_msg = (
            f"[{source}] Ошибка при выполнении инструкции #{instr_id} ({url}): {exc}"
        )
        logger.exception(err_msg)
        if log_record_id is not None:
            update_log_message(log_record_id, err_msg, is_success=False)
        else:
            db_log = create_log(
                LogCreate(
                    instr_id=instr_id,
                    is_success=False,
                    message=err_msg,
                )
            )
            log_record_id = db_log.id

        return {
            "session_id": session_id,
            "instr_id": instr_id,
            "is_success": False,
            "log_id": log_record_id,
            "message": err_msg,
        }

    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
        with _active_sessions_lock:
            _active_sessions.pop(session_id, None)


def launch_instruction_in_background(
    instr_id: int,
    url: str,
    steps: Dict[str, Any],
    cookie: Optional[CookieDataInput] = None,
    time_end: Optional[dt_time] = None,
    hold_seconds: int = 0,
    source: str = "scheduler",
) -> str:
    """Запускает выполнение инструкции в отдельном фоновом потоке."""
    thread = threading.Thread(
        target=execute_instruction_sync,
        kwargs={
            "instr_id": instr_id,
            "url": url,
            "steps": steps,
            "cookie": cookie,
            "time_end": time_end,
            "hold_seconds": hold_seconds,
            "source": source,
        },
        daemon=True,
        name=f"selenium-instr-{instr_id}-{source}",
    )
    thread.start()
    return thread.name
