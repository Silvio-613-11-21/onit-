from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Query, status

from src.controllers.singleactioncontroller import (
    list_single_actions,
    get_single_action,
    add_single_action,
    edit_single_action,
    remove_single_action,
)
from src.models.singleactionmodel import (
    SingleActionCreate,
    SingleActionUpdate,
    SingleActionResponse,
)

router = APIRouter(
    prefix="/single_actions",
    tags=["Single Actions (Нерегулярные инструкции)"],
)


@router.get(
    "",
    response_model=List[SingleActionResponse],
    summary="Получить все нерегулярные (разовые) инструкции",
)
async def get_single_actions(
    instr_id: Optional[int] = Query(default=None, description="Фильтр по ID инструкции"),
    action_date: Optional[date] = Query(
        default=None, description="Фильтр по дате (ГГГГ-ММ-ДД)"
    ),
    is_complete: Optional[bool] = Query(
        default=None, description="Фильтр по статусу выполнения"
    ),
):
    return await list_single_actions(
        instr_id=instr_id, action_date=action_date, is_complete=is_complete
    )


@router.get(
    "/{action_id}",
    response_model=SingleActionResponse,
    summary="Получить нерегулярную инструкцию по ID",
)
async def get_single_action_by_id_route(action_id: int):
    return await get_single_action(action_id)


@router.post(
    "",
    response_model=SingleActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать нерегулярную инструкцию",
)
async def create_single_action_route(data: SingleActionCreate):
    return await add_single_action(data)


@router.put(
    "/{action_id}",
    response_model=SingleActionResponse,
    summary="Обновить нерегулярную инструкцию",
)
async def update_single_action_route(action_id: int, data: SingleActionUpdate):
    return await edit_single_action(action_id, data)


@router.delete(
    "/{action_id}",
    summary="Удалить нерегулярную инструкцию",
)
async def delete_single_action_route(action_id: int):
    return await remove_single_action(action_id)
