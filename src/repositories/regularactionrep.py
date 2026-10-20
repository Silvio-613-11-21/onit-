from datetime import time
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.create_db import SessionLocal
from database.models import (
    RegularAction as RegularActionORM,
    Instruction as InstructionORM,
)
from src.models.regularactionmodel import RegularActionCreate, RegularActionUpdate


async def get_all_regular_actions(
    instr_id: Optional[int] = None,
    day: Optional[int] = None,
) -> List[RegularActionORM]:
    with SessionLocal() as session:
        stmt = select(RegularActionORM).order_by(
            RegularActionORM.day, RegularActionORM.time_start, RegularActionORM.id
        )
        if instr_id is not None:
            stmt = stmt.where(RegularActionORM.instr_id == instr_id)
        if day is not None:
            stmt = stmt.where(RegularActionORM.day == day)
        res = session.execute(stmt)
        return list(res.scalars().all())


async def get_regular_action_by_id(action_id: int) -> Optional[RegularActionORM]:
    with SessionLocal() as session:
        return session.get(RegularActionORM, action_id)


def create_regular_action(data: RegularActionCreate) -> RegularActionORM:
    with SessionLocal() as session:
        db_action = RegularActionORM(
            instr_id=data.instr_id,
            day=data.day,
            time_start=data.time_start,
            time_end=data.time_end,
        )
        session.add(db_action)
        session.commit()
        session.refresh(db_action)
        return db_action


def update_regular_action(
    action_id: int, data: RegularActionUpdate
) -> Optional[RegularActionORM]:
    with SessionLocal() as session:
        db_action = session.get(RegularActionORM, action_id)
        if not db_action:
            return None

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(db_action, field, value)

        session.commit()
        session.refresh(db_action)
        return db_action


def delete_regular_action(action_id: int) -> bool:
    with SessionLocal() as session:
        db_action = session.get(RegularActionORM, action_id)
        if not db_action:
            return False
        session.delete(db_action)
        session.commit()
        return True


def get_due_regular_actions(
    current_day: int, current_time: time
) -> List[RegularActionORM]:
    """Возвращает регулярные инструкции, у которых день недели и интервал времени совпадают с системными."""
    with SessionLocal() as session:
        stmt = (
            select(RegularActionORM)
            .options(
                joinedload(RegularActionORM.instruction).joinedload(
                    InstructionORM.step_rel
                ),
                joinedload(RegularActionORM.instruction).joinedload(
                    InstructionORM.cookie_rel
                ),
            )
            .where(
                RegularActionORM.day == current_day,
                RegularActionORM.time_start <= current_time,
                RegularActionORM.time_end >= current_time,
            )
            .order_by(RegularActionORM.time_start)
        )
        res = session.execute(stmt)
        return list(res.scalars().unique().all())
