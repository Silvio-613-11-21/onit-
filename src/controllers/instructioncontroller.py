from src.repositories.instuctionrep import get_all_instr, create_instr

from src.models.instructionmodel import Instruction

async def get_all_instructions ():
    return await get_all_instr() 

async def create_instruction (instr: Instruction): 
    create_instr(instr)