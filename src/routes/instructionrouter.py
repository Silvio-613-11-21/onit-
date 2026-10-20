from typing import Any, Dict, List
from fastapi import APIRouter, Body, status

from src.controllers.instructioncontroller import (
    get_all_instructions,
    get_instruction,
    create_instruction,
    update_instruction,
    delete_instruction,
    run_instruction_by_id,
)
from src.models.instructionmodel import (
    InstructionCreate,
    InstructionUpdate,
    InstructionResponse,
    InstructionRunRequest,
)

router = APIRouter(tags=["Instructions (Инструкции)"])


@router.get(
    "/instructions",
    response_model=List[InstructionResponse],
    summary="Получить все инструкции (вместе с привязанными steps и cookie)",
)
async def get_all_instr():
    return await get_all_instructions()


@router.get(
    "/instructions/{instr_id}",
    response_model=InstructionResponse,
    summary="Получить инструкцию по ID",
)
async def get_instr(instr_id: int):
    return await get_instruction(instr_id)


@router.post(
    "/create_instruction",
    response_model=InstructionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую инструкцию (связка url + step_id + cookie_id)",
)
async def create_instr_(instr: InstructionCreate):
    return await create_instruction(instr)


@router.post(
    "/instructions",
    response_model=InstructionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую инструкцию (REST)",
)
async def create_instr_rest(instr: InstructionCreate):
    return await create_instruction(instr)


@router.put(
    "/instructions/{instr_id}",
    response_model=InstructionResponse,
    summary="Обновить инструкцию по ID",
)
async def update_instr_(instr_id: int, instr: InstructionUpdate):
    return await update_instruction(instr_id, instr)


@router.delete(
    "/instructions/{instr_id}",
    summary="Удалить инструкцию по ID",
)
async def delete_instr_(instr_id: int):
    return await delete_instruction(instr_id)


@router.post(
    "/instructions/{instr_id}/run",
    summary="Запустить выполнение инструкции вручную через Selenium",
    description=(
        "Открывает браузер Selenium, переходит по URL инструкции, добавляет куки из привязанной записи "
        "таблицы `cookie` (если есть), последовательно ищет элементы для шагов из таблицы `step` "
        "по [текст, id, name, тэг, class, xpath], выполняет действия и удерживает браузер до time_end "
        "(или hold_seconds), после чего сохраняет запись в лог."
    ),
)
async def run_instr(
    instr_id: int,
    run_params: InstructionRunRequest = Body(default_factory=InstructionRunRequest),
) -> Dict[str, Any]:
    return await run_instruction_by_id(instr_id, run_params)
