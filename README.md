# OnIt — Автоматизация браузера по расписанию (FastAPI + SQLAlchemy + Selenium + PostgreSQL)

Сервис для выполнения инструкций в браузере через **Selenium** по расписанию (регулярному и разовому) с управлением через **Swagger UI** (`FastAPI`) и хранением данных в **PostgreSQL** (`SQLAlchemy`).

---

## Схема базы данных (без дублирования данных)

1. **`step` (Шаблоны шагов)**:
   - `id` — первичный ключ.
   - `title` — понятное название шаблона (например, `"Вход в МТС Линк и отключение камеры"`).
   - `steps` — шаги в формате JSON `{ "ключ_элемента": "действие" }`:
     - **Поиск элемента (`ключ`)**: программа последовательно проверяет стратегии поиска в порядке:
       `[текст, id, name, тэг, class, xpath]` и выбирает **первое совпадение**.
     - **Действие (`значение`)**:
       - `"click"` — клик по найденному элементу;
       - любая другая строка (или `"input:текст"` / `"send_keys:текст"`) — ввод текста (`send_keys`) в найденный элемент;
       - также поддерживаются `"clear"`, `"submit"`, `"enter"`, `"double_click"`, `"hover"`, `"wait:N"`.

2. **`cookie` (Наборы куки)**:
   - `id` — первичный ключ.
   - `title` — название профиля куки (например, `"Аккаунт МТС Линк"`).
   - `cookie` — данные куки в формате JSON:
     - **Рекомендуемый формат (массив объектов Selenium / браузерных расширений)**:
       `[{"name": "access", "value": "...", "domain": ".mts-link.ru", "path": "/"}]`
     - Также поддерживается простой словарь `{"name": "value"}`.

3. **`instruction` (Инструкции — связка URL + шаги + куки)**:
   - `id` — первичный ключ.
   - `url` — ссылка, которую открывает Selenium.
   - `step_id` — внешний ключ (`FK -> step.id`).
   - `cookie_id` — внешний ключ (`FK -> cookie.id`, опционально `null`).
   - Один и тот же набор шагов (`step_id`) и куки (`cookie_id`) можно привязывать к любому количеству разных `url` без дублирования!

4. **`regular_action` (Регулярное расписание)**:
   - `instr_id`, `day` (`0` = Понедельник … `6` = Воскресенье), `time_start`, `time_end`.
   - При совпадении системного дня недели и времени запускается браузер, выполняет шаги и **удерживает вкладку открытой до `time_end`**, после чего закрывает браузер.

5. **`single_action` (Нерегулярное / разовое расписание)**:
   - `instr_id`, `date`, `time_start`, `time_end`, `is_complete`.

6. **`log` (Логи выполнения)**:
   - `instr_id`, `date`, `time`, `is_success`, `message`.

---

## Настройка и запуск

### 1. Переменные окружения (`.env`)
```env
DATABASE_URL = postgresql+psycopg2://postgres:admin@localhost:5432/postgres
TEST_DATABASE_URL = postgresql+psycopg2://postgres:admin@localhost:5432/postgre-test
PORT=8080
HOST=localhost
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Запуск сервера FastAPI
```bash
python main.py
# или:
uvicorn main:app --host 127.0.0.1 --port 8080 --reload
```

### 4. Swagger UI
- `http://localhost:8080/docs` (или `http://localhost:8080/`)

---

## Тестирование

Тесты разделены на отдельные модули в папке `tests/`:
- `tests/conftest.py` — конфигурация тестового окружения и подключение к тестовой базе PostgreSQL (`TEST_DATABASE_URL`).
- `tests/test_unit.py` — **5 unit-тестов** (изолированная проверка функций поиска локаторов, нормализации куки, экранирования XPath, действий Selenium и валидации Pydantic-моделей без обращения к БД).
- `tests/test_integration.py` — **3 integration-теста** (проверка связки FastAPI + PostgreSQL `postgre-test` + планировщика + Selenium-исполнителя).

### Запуск всех тестов (5 unit + 3 integration)
В терминале из корневой папки проекта выполните:
```bash
pytest -v
```

### Запуск только Unit-тестов
```bash
pytest tests/test_unit.py -v
```

### Запуск только Integration-тестов (требуется запущенный PostgreSQL с базой `postgre-test`)
```bash
pytest tests/test_integration.py -v
```

*(Также любой из файлов `tests/test_unit.py` или `tests/test_integration.py` можно запустить напрямую кнопкой **▶ Run Python File** в VS Code).*
