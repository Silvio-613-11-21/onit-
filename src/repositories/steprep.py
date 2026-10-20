from typing import List, Optional
from sqlalchemy import select

from database.create_db import SessionLocal
from database.models import Step as StepORM
from src.models.stepmodel import StepCreate, StepUpdate


async def get_all_steps() -> List[StepORM]:
    with SessionLocal() as session:
        res = session.execute(select(StepORM).order_by(StepORM.id))
        return list(res.scalars().all())


async def get_step_by_id(step_id: int) -> Optional[StepORM]:
    with SessionLocal() as session:
        return session.get(StepORM, step_id)


def create_step(data: StepCreate) -> StepORM:
    with SessionLocal() as session:
        db_step = StepORM(
            title=data.title,
            steps=data.steps,
        )
        session.add(db_step)
        session.commit()
        session.refresh(db_step)
        return db_step


def update_step(step_id: int, data: StepUpdate) -> Optional[StepORM]:
    with SessionLocal() as session:
        db_step = session.get(StepORM, step_id)
        if not db_step:
            return None

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(db_step, field, value)

        session.commit()
        session.refresh(db_step)
        return db_step


def delete_step(step_id: int) -> bool:
    with SessionLocal() as session:
        db_step = session.get(StepORM, step_id)
        if not db_step:
            return False
        session.delete(db_step)
        session.commit()
        return True
