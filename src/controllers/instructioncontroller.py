import os
from typing import Any, Dict, List
from fastapi import HTTPException, status

from src.repositories.instuctionrep import (
    get_all_instr,
    get_instr_by_id,
    create_instr,
    update_instr,
    delete_instr,
)
from src.models.instructionmodel import (
    InstructionCreate,
    InstructionUpdate,
    InstructionRunRequest,
)
from src.services.selenium_service import (
    execute_instruction_sync,
    launch_instruction_in_background,
    parse_cookie_file_content,
)


async def get_all_instructions():
    return await get_all_instr()


async def get_instruction(instr_id: int):
    instr = await get_instr_by_id(instr_id)
    if not instr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Инструкция с id={instr_id} не найдена",
        )
    return instr


async def create_instruction(instr: InstructionCreate):
    return create_instr(instr)


async def update_instruction(instr_id: int, instr_data: InstructionUpdate):
    updated = update_instr(instr_id, instr_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Инструкция с id={instr_id} не найдена",
        )
    return updated


async def delete_instruction(instr_id: int) -> Dict[str, Any]:
    deleted = delete_instr(instr_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Инструкция с id={instr_id} не найдена",
        )
    return {"status": "deleted", "id": instr_id}


async def run_instruction_by_id(
    instr_id: int, run_params: InstructionRunRequest
) -> Dict[str, Any]:
    instr = await get_instr_by_id(instr_id)
    if not instr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Инструкция с id={instr_id} не найдена",
        )

    if run_params.background:
        thread_name = launch_instruction_in_background(
            instr_id=instr.id,
            url=instr.url,
            steps=instr.steps,
            cookie=instr.cookie,
            time_end=run_params.time_end,
            hold_seconds=run_params.hold_seconds,
            source="manual_api",
        )
        return {
            "status": "started_in_background",
            "instr_id": instr.id,
            "url": instr.url,
            "time_end": str(run_params.time_end) if run_params.time_end else None,
            "hold_seconds": run_params.hold_seconds,
            "thread": thread_name,
        }

    return execute_instruction_sync(
        instr_id=instr.id,
        url=instr.url,
        steps=instr.steps,
        cookie=instr.cookie,
        time_end=run_params.time_end,
        hold_seconds=run_params.hold_seconds,
        source="manual_api_sync",
    )


async def parse_local_cookie_file(file_path: str = "cookie.txt") -> Dict[str, str]:
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл '{file_path}' не найден",
        )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_cookie_file_content(content)
