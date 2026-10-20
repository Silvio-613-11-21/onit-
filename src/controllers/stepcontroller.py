from typing import Any, Dict
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.repositories.steprep import (
    get_all_steps,
    get_step_by_id,
    create_step,
    update_step,
    delete_step,
)
from src.models.stepmodel import StepCreate, StepUpdate


async def list_steps():
    return await get_all_steps()


async def get_step(step_id: int):
    step_obj = await get_step_by_id(step_id)
    if not step_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Набор шагов с id={step_id} не найден",
        )
    return step_obj


async def add_step(data: StepCreate):
    return create_step(data)


async def edit_step(step_id: int, data: StepUpdate):
    updated = update_step(step_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Набор шагов с id={step_id} не найден",
        )
    return updated


async def remove_step(step_id: int) -> Dict[str, Any]:
    try:
        deleted = delete_step(step_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя удалить набор шагов id={step_id}, так как он используется в существующих инструкциях",
        )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Набор шагов с id={step_id} не найден",
        )
    return {"status": "deleted", "id": step_id}
