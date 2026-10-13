from fastapi import APIRouter

from src.controllers.instructioncontroller import get_all_instructions, create_instr

from src.models.instructionmodel import Instruction

router = APIRouter()

@router.get('/instructions') 
async def get_all_instr():
    return await get_all_instructions()

@router.post('/create_instruction')
async def create_instr_(instr: Instruction):
    create_instr(instr)