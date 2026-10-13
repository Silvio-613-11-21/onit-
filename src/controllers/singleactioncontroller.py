from datetime import date
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

from src.repositories.instuctionrep import get_instr_by_id
from src.repositories.singleactionrep import (
    get_all_single_actions,
    get_single_action_by_id,
    create_single_action,
    update_single_action,
    delete_single_action,
)
from src.models.singleactionmodel import SingleActionCreate, SingleActionUpdate


async def list_single_actions(
    instr_id: Optional[int] = None,
    action_date: Optional[date] = None,
    is_complete: Optional[bool] = None,
):
    return await get_all_single_actions(
        instr_id=instr_id, action_date=action_date, is_complete=is_complete
    )


async def get_single_action(action_id: int):
    action = await get_single_action_by_id(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Нерегулярная инструкция с id={action_id} не найдена",
        )
    return action


async def add_single_action(data: SingleActionCreate):
    instr = await get_instr_by_id(data.instr_id)
    if not instr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Инструкция с id={data.instr_id} не найдена",
        )
    if data.time_end < data.time_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="time_end не может быть меньше time_start",
        )
    return create_single_action(data)


async def edit_single_action(action_id: int, data: SingleActionUpdate):
    existing = await get_single_action_by_id(action_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Нерегулярная инструкция с id={action_id} не найдена",
        )
    if data.instr_id is not None:
        instr = await get_instr_by_id(data.instr_id)
        if not instr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Инструкция с id={data.instr_id} не найдена",
            )
    new_start = data.time_start if data.time_start is not None else existing.time_start
    new_end = data.time_end if data.time_end is not None else existing.time_end
    if new_end < new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="time_end не может быть меньше time_start",
        )
    return update_single_action(action_id, data)


async def remove_single_action(action_id: int) -> Dict[str, Any]:
    deleted = delete_single_action(action_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Нерегулярная инструкция с id={action_id} не найдена",
        )
    return {"status": "deleted", "id": action_id}
