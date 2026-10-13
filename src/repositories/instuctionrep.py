import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import select 

from database.models import Instruction
from src.models.instructionmodel import Instruction as Instr_

load_dotenv()  
url = os.getenv("DATABASE_URL")
if(not url):
    raise ValueError("Ошибка соединения с бд")
engine = create_engine(url=url, echo=True)
session = Session(engine)


async def get_all_instr ():
    return  select(Instruction)


def create_instr (instr: Instr_): 
    with session:
        session.add(instr) 
        session.commit()

    return instr 


