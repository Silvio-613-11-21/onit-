from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from src.services.scheduler_service import scheduler_service
from src.services.selenium_service import get_active_sessions, stop_active_session

router = APIRouter(
    prefix="/scheduler",
    tags=["Scheduler (Планировщик и активные браузеры)"],
)


@router.get(
    "/status",
    summary="Статус планировщика, системное время и активные сессии Selenium",
)
async def get_scheduler_status() -> Dict[str, Any]:
    return scheduler_service.status()


@router.post(
    "/check-now",
    summary="Принудительно сверить системное время с БД и запустить подходящие инструкции",
)
async def trigger_scheduler_check_now() -> Dict[str, Any]:
    return scheduler_service.check_and_trigger_now()


@router.get(
    "/sessions",
    summary="Список открытых в данный момент браузеров Selenium",
)
async def list_active_sessions():
    return get_active_sessions()


@router.post(
    "/sessions/{session_id}/stop",
    summary="Досрочно завершить и закрыть браузер активной сессии",
)
async def stop_browser_session(session_id: str) -> Dict[str, Any]:
    stopped = stop_active_session(session_id)
    if not stopped:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Активная сессия '{session_id}' не найдена",
        )
    return {"status": "stopping", "session_id": session_id}
