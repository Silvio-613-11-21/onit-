from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Query, status

from src.controllers.logcontroller import (
    list_logs,
    get_log,
    add_log,
    remove_log,
    remove_all_logs,
)
from src.models.logmodel import LogCreate, LogResponse

router = APIRouter(
    prefix="/logs",
    tags=["Logs (Логи выполнения)"],
)


@router.get(
    "",
    response_model=List[LogResponse],
    summary="Получить список логов",
)
async def get_logs_route(
    instr_id: Optional[int] = Query(default=None, description="Фильтр по ID инструкции"),
    log_date: Optional[date] = Query(
        default=None, description="Фильтр по дате (ГГГГ-ММ-ДД)"
    ),
    is_success: Optional[bool] = Query(
        default=None, description="Фильтр по успешности выполнения"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Лимит записей"),
):
    return await list_logs(
        instr_id=instr_id,
        log_date=log_date,
        is_success=is_success,
        limit=limit,
    )


@router.get(
    "/{log_id}",
    response_model=LogResponse,
    summary="Получить запись лога по ID",
)
async def get_log_by_id_route(log_id: int):
    return await get_log(log_id)


@router.post(
    "",
    response_model=LogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать запись лога вручную",
)
async def create_log_route(data: LogCreate):
    return await add_log(data)


@router.delete(
    "/{log_id}",
    summary="Удалить запись лога по ID",
)
async def delete_log_route(log_id: int):
    return await remove_log(log_id)


@router.delete(
    "",
    summary="Очистить логи (все или по конкретной инструкции)",
)
async def clear_logs_route(
    instr_id: Optional[int] = Query(
        default=None, description="Если указан — удалить логи только этой инструкции"
    ),
):
    return await remove_all_logs(instr_id=instr_id)
