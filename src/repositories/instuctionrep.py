from typing import List, Optional
from sqlalchemy import select

from database.create_db import SessionLocal
from database.models import Instruction as InstructionORM
from src.models.instructionmodel import InstructionCreate, InstructionUpdate


async def get_all_instr() -> List[InstructionORM]:
    with SessionLocal() as session:
        res = session.execute(select(InstructionORM).order_by(InstructionORM.id))
        return list(res.scalars().all())


async def get_instr_by_id(instr_id: int) -> Optional[InstructionORM]:
    with SessionLocal() as session:
        return session.get(InstructionORM, instr_id)


def get_instr_by_id_sync(instr_id: int) -> Optional[InstructionORM]:
    with SessionLocal() as session:
        return session.get(InstructionORM, instr_id)


def create_instr(instr: InstructionCreate) -> InstructionORM:
    with SessionLocal() as session:
        db_instr = InstructionORM(
            url=instr.url,
            steps=instr.steps,
            cookie=instr.cookie,
        )
        session.add(db_instr)
        session.commit()
        session.refresh(db_instr)
        return db_instr


def update_instr(instr_id: int, instr_data: InstructionUpdate) -> Optional[InstructionORM]:
    with SessionLocal() as session:
        db_instr = session.get(InstructionORM, instr_id)
        if not db_instr:
            return None

        update_fields = instr_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(db_instr, field, value)

        session.commit()
        session.refresh(db_instr)
        return db_instr


def delete_instr(instr_id: int) -> bool:
    with SessionLocal() as session:
        db_instr = session.get(InstructionORM, instr_id)
        if not db_instr:
            return False
        session.delete(db_instr)
        session.commit()
        return True
