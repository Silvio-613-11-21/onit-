from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.create_db import SessionLocal
from database.models import Instruction as InstructionORM
from src.models.instructionmodel import InstructionCreate, InstructionUpdate


async def get_all_instr() -> List[InstructionORM]:
    with SessionLocal() as session:
        stmt = (
            select(InstructionORM)
            .options(
                joinedload(InstructionORM.step_rel),
                joinedload(InstructionORM.cookie_rel),
            )
            .order_by(InstructionORM.id)
        )
        res = session.execute(stmt)
        return list(res.scalars().all())


async def get_instr_by_id(instr_id: int) -> Optional[InstructionORM]:
    with SessionLocal() as session:
        stmt = (
            select(InstructionORM)
            .options(
                joinedload(InstructionORM.step_rel),
                joinedload(InstructionORM.cookie_rel),
            )
            .where(InstructionORM.id == instr_id)
        )
        return session.execute(stmt).scalar_one_or_none()


def get_instr_by_id_sync(instr_id: int) -> Optional[InstructionORM]:
    with SessionLocal() as session:
        stmt = (
            select(InstructionORM)
            .options(
                joinedload(InstructionORM.step_rel),
                joinedload(InstructionORM.cookie_rel),
            )
            .where(InstructionORM.id == instr_id)
        )
        return session.execute(stmt).scalar_one_or_none()


def create_instr(instr: InstructionCreate) -> InstructionORM:
    with SessionLocal() as session:
        db_instr = InstructionORM(
            url=instr.url,
            step_id=instr.step_id,
            cookie_id=instr.cookie_id,
        )
        session.add(db_instr)
        session.commit()
        session.refresh(db_instr)
        # Подгружаем связанные step_rel и cookie_rel перед закрытием сессии
        _ = db_instr.step_rel
        _ = db_instr.cookie_rel
        return db_instr


def update_instr(
    instr_id: int, instr_data: InstructionUpdate
) -> Optional[InstructionORM]:
    with SessionLocal() as session:
        db_instr = session.get(InstructionORM, instr_id)
        if not db_instr:
            return None

        update_fields = instr_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(db_instr, field, value)

        session.commit()
        session.refresh(db_instr)
        _ = db_instr.step_rel
        _ = db_instr.cookie_rel
        return db_instr


def delete_instr(instr_id: int) -> bool:
    with SessionLocal() as session:
        db_instr = session.get(InstructionORM, instr_id)
        if not db_instr:
            return False
        session.delete(db_instr)
        session.commit()
        return True
