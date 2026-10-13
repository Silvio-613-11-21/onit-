import os
import threading
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set, Tuple

from src.repositories.regularactionrep import get_due_regular_actions
from src.repositories.singleactionrep import (
    get_due_single_actions,
    mark_single_action_complete,
)
from src.services.selenium_service import (
    launch_instruction_in_background,
    get_active_sessions,
    is_instruction_currently_running,
)

logger = logging.getLogger(__name__)

DAYS_RU = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}


class SchedulerService:
    """
    Фоновый планировщик, который сверяет системную дату/время с таблицами
    `regular_action` и `single_action` в БД и при совпадении запускает инструкции.
    """

    def __init__(self, check_interval: int = 10) -> None:
        self.check_interval = check_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        # Хранит (regular_action_id, date_iso, time_start_iso), уже запущенные сегодня
        self._triggered_regular_today: Set[Tuple[int, str, str]] = set()
        self._last_check_at: Optional[str] = None
        self._last_error: Optional[str] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="instruction-scheduler",
        )
        self._thread.start()
        logger.info(
            "Планировщик инструкций запущен (интервал проверки: %s сек.)",
            self.check_interval,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        logger.info("Планировщик инструкций остановлен.")

    def _cleanup_old_dates(self, today_iso: str) -> None:
        with self._lock:
            to_remove = {
                item for item in self._triggered_regular_today if item[1] != today_iso
            }
            self._triggered_regular_today -= to_remove

    def check_and_trigger_now(self) -> Dict[str, Any]:
        """
        Сверяет текущее системное время с БД (`regular_action` и `single_action`)
        и запускает совпавшие инструкции.
        """
        now = datetime.now()
        current_date: date = now.date()
        current_time = now.time().replace(microsecond=0)
        current_day: int = now.weekday()  # 0 = Пн ... 6 = Вс
        today_iso = current_date.isoformat()

        self._last_check_at = now.isoformat(timespec="seconds")
        self._cleanup_old_dates(today_iso)

        launched_single: List[Dict[str, Any]] = []
        launched_regular: List[Dict[str, Any]] = []

        try:
            # 1. Проверка нерегулярных (разовых) инструкций (single_action)
            due_singles = get_due_single_actions(current_date, current_time)
            for single in due_singles:
                source_tag = f"single_action:{single.id}"
                if is_instruction_currently_running(single.instr_id, source=source_tag):
                    continue

                instr = single.instruction
                if not instr:
                    continue

                # Отмечаем как выполненную и запускаем браузер до time_end
                mark_single_action_complete(single.id, True)
                thread_name = launch_instruction_in_background(
                    instr_id=instr.id,
                    url=instr.url,
                    steps=instr.steps,
                    cookie=instr.cookie,
                    time_end=single.time_end,
                    source=source_tag,
                )
                launched_single.append(
                    {
                        "single_action_id": single.id,
                        "instr_id": instr.id,
                        "url": instr.url,
                        "date": str(single.date),
                        "time_start": str(single.time_start),
                        "time_end": str(single.time_end),
                        "thread": thread_name,
                    }
                )

            # 2. Проверка регулярных инструкций (regular_action)
            due_regulars = get_due_regular_actions(current_day, current_time)
            for reg in due_regulars:
                key = (reg.id, today_iso, str(reg.time_start))
                source_tag = f"regular_action:{reg.id}"

                with self._lock:
                    already_triggered = key in self._triggered_regular_today

                if already_triggered or is_instruction_currently_running(
                    reg.instr_id, source=source_tag
                ):
                    continue

                instr = reg.instruction
                if not instr:
                    continue

                with self._lock:
                    self._triggered_regular_today.add(key)

                thread_name = launch_instruction_in_background(
                    instr_id=instr.id,
                    url=instr.url,
                    steps=instr.steps,
                    cookie=instr.cookie,
                    time_end=reg.time_end,
                    source=source_tag,
                )
                launched_regular.append(
                    {
                        "regular_action_id": reg.id,
                        "instr_id": instr.id,
                        "url": instr.url,
                        "day": reg.day,
                        "day_name": DAYS_RU.get(reg.day, str(reg.day)),
                        "time_start": str(reg.time_start),
                        "time_end": str(reg.time_end),
                        "thread": thread_name,
                    }
                )

            self._last_error = None

        except Exception as exc:
            self._last_error = str(exc)
            logger.warning("Ошибка при проверке расписания в БД: %s", exc)

        return {
            "checked_at": self._last_check_at,
            "system_date": today_iso,
            "system_time": str(current_time),
            "system_day": current_day,
            "system_day_name": DAYS_RU.get(current_day, str(current_day)),
            "launched_single_actions": launched_single,
            "launched_regular_actions": launched_regular,
            "error": self._last_error,
        }

    def status(self) -> Dict[str, Any]:
        now = datetime.now()
        current_day = now.weekday()
        return {
            "scheduler_running": bool(self._thread and self._thread.is_alive()),
            "check_interval_seconds": self.check_interval,
            "last_check_at": self._last_check_at,
            "last_error": self._last_error,
            "system_date": now.date().isoformat(),
            "system_time": now.time().replace(microsecond=0).isoformat(),
            "system_day": current_day,
            "system_day_name": DAYS_RU.get(current_day, str(current_day)),
            "active_browser_sessions": get_active_sessions(),
            "triggered_regular_today": [
                {
                    "regular_action_id": item[0],
                    "date": item[1],
                    "time_start": item[2],
                }
                for item in sorted(self._triggered_regular_today)
            ],
        }

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self.check_and_trigger_now()
            self._stop_event.wait(timeout=float(self.check_interval))


check_interval_env = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "10"))
scheduler_service = SchedulerService(check_interval=check_interval_env)
