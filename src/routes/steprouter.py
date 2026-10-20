from typing import List
from fastapi import APIRouter, status

from src.controllers.stepcontroller import (
    list_steps,
    get_step,
    add_step,
    edit_step,
    remove_step,
)
from src.models.stepmodel import StepCreate, StepUpdate, StepResponse

router = APIRouter(
    prefix="/steps",
    tags=["Steps (Шаблоны шагов)"],
)


@router.get(
    "",
    response_model=List[StepResponse],
    summary="Получить все шаблоны шагов",
)
async def get_steps_route():
    return await list_steps()


@router.get(
    "/{step_id}",
    response_model=StepResponse,
    summary="Получить шаблон шагов по ID",
)
async def get_step_by_id_route(step_id: int):
    return await get_step(step_id)


@router.post(
    "",
    response_model=StepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый шаблон шагов",
)
async def create_step_route(data: StepCreate):
    return await add_step(data)


@router.put(
    "/{step_id}",
    response_model=StepResponse,
    summary="Обновить шаблон шагов",
)
async def update_step_route(step_id: int, data: StepUpdate):
    return await edit_step(step_id, data)


@router.delete(
    "/{step_id}",
    summary="Удалить шаблон шагов",
)
async def delete_step_route(step_id: int):
    return await remove_step(step_id)
