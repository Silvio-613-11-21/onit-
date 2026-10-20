from typing import Any, Dict, Optional
from fastapi import HTTPException, status

from src.repositories.instuctionrep import get_instr_by_id
from src.repositories.regularactionrep import (
    get_all_regular_actions,
    get_regular_action_by_id,
    create_regular_action,
    update_regular_action,
    delete_regular_action,
)
from src.models.regularactionmodel import RegularActionCreate, RegularActionUpdate


async def list_regular_actions(
    instr_id: Optional[int] = None, day: Optional[int] = None
):
    return await get_all_regular_actions(instr_id=instr_id, day=day)


async def get_regular_action(action_id: int):
    action = await get_regular_action_by_id(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Регулярная инструкция с id={action_id} не найдена",
        )
    return action


async def add_regular_action(data: RegularActionCreate):
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
    return create_regular_action(data)


async def edit_regular_action(action_id: int, data: RegularActionUpdate):
    existing = await get_regular_action_by_id(action_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Регулярная инструкция с id={action_id} не найдена",
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
    return update_regular_action(action_id, data)


async def remove_regular_action(action_id: int) -> Dict[str, Any]:
    deleted = delete_regular_action(action_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Регулярная инструкция с id={action_id} не найдена",
        )
    return {"status": "deleted", "id": action_id}
