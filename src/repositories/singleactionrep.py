from datetime import date, time
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.create_db import SessionLocal
from database.models import (
    SingleAction as SingleActionORM,
    Instruction as InstructionORM,
)
from src.models.singleactionmodel import SingleActionCreate, SingleActionUpdate


async def get_all_single_actions(
    instr_id: Optional[int] = None,
    action_date: Optional[date] = None,
    is_complete: Optional[bool] = None,
) -> List[SingleActionORM]:
    with SessionLocal() as session:
        stmt = select(SingleActionORM).order_by(
            SingleActionORM.date, SingleActionORM.time_start, SingleActionORM.id
        )
        if instr_id is not None:
            stmt = stmt.where(SingleActionORM.instr_id == instr_id)
        if action_date is not None:
            stmt = stmt.where(SingleActionORM.date == action_date)
        if is_complete is not None:
            stmt = stmt.where(SingleActionORM.is_complete == is_complete)
        res = session.execute(stmt)
        return list(res.scalars().all())


async def get_single_action_by_id(action_id: int) -> Optional[SingleActionORM]:
    with SessionLocal() as session:
        return session.get(SingleActionORM, action_id)


def create_single_action(data: SingleActionCreate) -> SingleActionORM:
    with SessionLocal() as session:
        db_action = SingleActionORM(
            instr_id=data.instr_id,
            date=data.date,
            time_start=data.time_start,
            time_end=data.time_end,
            is_complete=data.is_complete,
        )
        session.add(db_action)
        session.commit()
        session.refresh(db_action)
        return db_action


def update_single_action(
    action_id: int, data: SingleActionUpdate
) -> Optional[SingleActionORM]:
    with SessionLocal() as session:
        db_action = session.get(SingleActionORM, action_id)
        if not db_action:
            return None

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(db_action, field, value)

        session.commit()
        session.refresh(db_action)
        return db_action


def delete_single_action(action_id: int) -> bool:
    with SessionLocal() as session:
        db_action = session.get(SingleActionORM, action_id)
        if not db_action:
            return False
        session.delete(db_action)
        session.commit()
        return True


def get_due_single_actions(
    current_date: date, current_time: time
) -> List[SingleActionORM]:
    """Возвращает невыполненные разовые инструкции на текущую дату и время."""
    with SessionLocal() as session:
        stmt = (
            select(SingleActionORM)
            .options(
                joinedload(SingleActionORM.instruction).joinedload(
                    InstructionORM.step_rel
                ),
                joinedload(SingleActionORM.instruction).joinedload(
                    InstructionORM.cookie_rel
                ),
            )
            .where(
                SingleActionORM.is_complete.is_(False),
                SingleActionORM.date == current_date,
                SingleActionORM.time_start <= current_time,
                SingleActionORM.time_end >= current_time,
            )
            .order_by(SingleActionORM.time_start)
        )
        res = session.execute(stmt)
        return list(res.scalars().unique().all())


def mark_single_action_complete(
    action_id: int, is_complete: bool = True
) -> Optional[SingleActionORM]:
    with SessionLocal() as session:
        db_action = session.get(SingleActionORM, action_id)
        if not db_action:
            return None
        db_action.is_complete = is_complete
        session.commit()
        session.refresh(db_action)
        return db_action
