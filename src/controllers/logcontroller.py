from datetime import date
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

from src.repositories.instuctionrep import get_instr_by_id
from src.repositories.logrep import (
    get_all_logs,
    get_log_by_id,
    create_log,
    delete_log,
    clear_logs,
)
from src.models.logmodel import LogCreate


async def list_logs(
    instr_id: Optional[int] = None,
    log_date: Optional[date] = None,
    is_success: Optional[bool] = None,
    limit: int = 100,
):
    return await get_all_logs(
        instr_id=instr_id,
        log_date=log_date,
        is_success=is_success,
        limit=limit,
    )


async def get_log(log_id: int):
    log_item = await get_log_by_id(log_id)
    if not log_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Лог с id={log_id} не найден",
        )
    return log_item


async def add_log(data: LogCreate):
    instr = await get_instr_by_id(data.instr_id)
    if not instr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Инструкция с id={data.instr_id} не найдена",
        )
    return create_log(data)


async def remove_log(log_id: int) -> Dict[str, Any]:
    deleted = delete_log(log_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Лог с id={log_id} не найден",
        )
    return {"status": "deleted", "id": log_id}


async def remove_all_logs(instr_id: Optional[int] = None) -> Dict[str, Any]:
    count = clear_logs(instr_id=instr_id)
    return {"status": "cleared", "deleted_count": count}
