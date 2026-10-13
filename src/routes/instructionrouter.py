from fastapi import APIRouter

from src.controllers.instructioncontroller import get_all_instructions

router = APIRouter()

@router.get('/instructions') 
async def get_all_instr():

    return await get_all_instructions()