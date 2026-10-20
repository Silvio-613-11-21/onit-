from typing import Any, Dict
from fastapi import HTTPException, status

from src.repositories.instuctionrep import (
    get_all_instr,
    get_instr_by_id,
    create_instr,
    update_instr,
    delete_instr,
)
from src.repositories.steprep import get_step_by_id
from src.repositories.cookierep import get_cookie_by_id
from src.models.instructionmodel import (
    InstructionCreate,
    InstructionUpdate,
    InstructionRunRequest,
)
from src.services.selenium_service import (
    execute_instruction_sync,
    launch_instruction_in_background,
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
    step_obj = await get_step_by_id(instr.step_id)
    if not step_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Набор шагов с id={instr.step_id} не найден в таблице step",
        )
    if instr.cookie_id is not None:
        cookie_obj = await get_cookie_by_id(instr.cookie_id)
        if not cookie_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Набор куки с id={instr.cookie_id} не найден в таблице cookie",
            )
    return create_instr(instr)


async def update_instruction(instr_id: int, instr_data: InstructionUpdate):
    existing = await get_instr_by_id(instr_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Инструкция с id={instr_id} не найдена",
        )
    if instr_data.step_id is not None:
        step_obj = await get_step_by_id(instr_data.step_id)
        if not step_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Набор шагов с id={instr_data.step_id} не найден в таблице step",
            )
    if instr_data.cookie_id is not None:
        cookie_obj = await get_cookie_by_id(instr_data.cookie_id)
        if not cookie_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Набор куки с id={instr_data.cookie_id} не найден в таблице cookie",
            )
    return update_instr(instr_id, instr_data)


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
            "step_id": instr.step_id,
            "cookie_id": instr.cookie_id,
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
