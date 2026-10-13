from typing import Any, Dict, List
from fastapi import APIRouter, Body, status

from src.controllers.instructioncontroller import (
    get_all_instructions,
    get_instruction,
    create_instruction,
    update_instruction,
    delete_instruction,
    run_instruction_by_id,
    parse_local_cookie_file,
)
from src.models.instructionmodel import (
    InstructionCreate,
    InstructionUpdate,
    InstructionResponse,
    InstructionRunRequest,
)
from src.services.selenium_service import parse_cookie_file_content

router = APIRouter(tags=["Instructions (Инструкции)"])


@router.get(
    "/instructions",
    response_model=List[InstructionResponse],
    summary="Получить все инструкции",
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
    summary="Создать новую инструкцию",
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
        "Открывает браузер Selenium, переходит по URL инструкции, добавляет куки из БД (если есть), "
        "последовательно ищет элементы по [текст, id, name, тэг, class, xpath], выполняет действия "
        "и удерживает браузер до time_end (или hold_seconds), после чего сохраняет запись в лог."
    ),
)
async def run_instr(
    instr_id: int,
    run_params: InstructionRunRequest = Body(default_factory=InstructionRunRequest),
) -> Dict[str, Any]:
    return await run_instruction_by_id(instr_id, run_params)


@router.get(
    "/cookies/from-file",
    summary="Спарсить локальный файл cookie.txt в JSON ключ-значение",
    description="Читает файл cookie.txt и возвращает JSON словарь {name: value}, готовый для вставки в поле cookie инструкции.",
)
async def get_cookies_from_file(file_path: str = "cookie.txt") -> Dict[str, str]:
    return await parse_local_cookie_file(file_path)


@router.post(
    "/cookies/parse-text",
    summary="Преобразовать текст куки (tab-separated) в JSON ключ-значение",
)
async def parse_cookies_text(
    raw_text: str = Body(..., media_type="text/plain", description="Строки из cookie.txt")
) -> Dict[str, str]:
    return parse_cookie_file_content(raw_text)
