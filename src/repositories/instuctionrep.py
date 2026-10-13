import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import select 

from database.models import Instruction
from src.models.instructionmodel import Instruction 

load_dotenv()  
url = os.getenv("DATABASE_URL")
if(not url):
    raise ValueError("Ошибка соединения с бд")
engine = create_engine(url=url, echo=True)
session = Session(engine)


async def get_all_instr ():
    res = session.execute( select(Instruction) )
    return  res.scalar()


def create_instr (instr: Instruction): 
    with session:
        session.add(instr) 
        session.commit()

    # return instr 


