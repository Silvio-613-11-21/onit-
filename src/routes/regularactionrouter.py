from typing import List, Optional
from fastapi import APIRouter, Query, status

from src.controllers.regularactioncontroller import (
    list_regular_actions,
    get_regular_action,
    add_regular_action,
    edit_regular_action,
    remove_regular_action,
)
from src.models.regularactionmodel import (
    RegularActionCreate,
    RegularActionUpdate,
    RegularActionResponse,
)

router = APIRouter(
    prefix="/regular_actions",
    tags=["Regular Actions (Регулярные инструкции)"],
)


@router.get(
    "",
    response_model=List[RegularActionResponse],
    summary="Получить все регулярные инструкции",
)
async def get_regular_actions(
    instr_id: Optional[int] = Query(default=None, description="Фильтр по ID инструкции"),
    day: Optional[int] = Query(
        default=None, ge=0, le=6, description="Фильтр по дню недели (0=Пн ... 6=Вс)"
    ),
):
    return await list_regular_actions(instr_id=instr_id, day=day)


@router.get(
    "/{action_id}",
    response_model=RegularActionResponse,
    summary="Получить регулярную инструкцию по ID",
)
async def get_regular_action_by_id_route(action_id: int):
    return await get_regular_action(action_id)


@router.post(
    "",
    response_model=RegularActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать регулярную инструкцию",
)
async def create_regular_action_route(data: RegularActionCreate):
    return await add_regular_action(data)


@router.put(
    "/{action_id}",
    response_model=RegularActionResponse,
    summary="Обновить регулярную инструкцию",
)
async def update_regular_action_route(action_id: int, data: RegularActionUpdate):
    return await edit_regular_action(action_id, data)


@router.delete(
    "/{action_id}",
    summary="Удалить регулярную инструкцию",
)
async def delete_regular_action_route(action_id: int):
    return await remove_regular_action(action_id)
