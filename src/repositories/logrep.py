from datetime import datetime, date, time
from typing import List, Optional
from sqlalchemy import select, delete

from database.create_db import SessionLocal
from database.models import Log as LogORM
from src.models.logmodel import LogCreate


async def get_all_logs(
    instr_id: Optional[int] = None,
    log_date: Optional[date] = None,
    is_success: Optional[bool] = None,
    limit: int = 100,
) -> List[LogORM]:
    with SessionLocal() as session:
        stmt = select(LogORM).order_by(LogORM.date.desc(), LogORM.time.desc(), LogORM.id.desc())
        if instr_id is not None:
            stmt = stmt.where(LogORM.instr_id == instr_id)
        if log_date is not None:
            stmt = stmt.where(LogORM.date == log_date)
        if is_success is not None:
            stmt = stmt.where(LogORM.is_success == is_success)
        if limit > 0:
            stmt = stmt.limit(limit)
        res = session.execute(stmt)
        return list(res.scalars().all())


async def get_log_by_id(log_id: int) -> Optional[LogORM]:
    with SessionLocal() as session:
        return session.get(LogORM, log_id)


def create_log(data: LogCreate) -> LogORM:
    now = datetime.now()
    with SessionLocal() as session:
        db_log = LogORM(
            instr_id=data.instr_id,
            date=data.date or now.date(),
            time=data.time or now.time().replace(microsecond=0),
            is_success=data.is_success,
            message=data.message,
        )
        session.add(db_log)
        session.commit()
        session.refresh(db_log)
        return db_log


def update_log_message(
    log_id: int, message: str, is_success: Optional[bool] = None
) -> Optional[LogORM]:
    with SessionLocal() as session:
        db_log = session.get(LogORM, log_id)
        if not db_log:
            return None
        db_log.message = message
        if is_success is not None:
            db_log.is_success = is_success
        session.commit()
        session.refresh(db_log)
        return db_log


def delete_log(log_id: int) -> bool:
    with SessionLocal() as session:
        db_log = session.get(LogORM, log_id)
        if not db_log:
            return False
        session.delete(db_log)
        session.commit()
        return True


def clear_logs(instr_id: Optional[int] = None) -> int:
    with SessionLocal() as session:
        stmt = delete(LogORM)
        if instr_id is not None:
            stmt = stmt.where(LogORM.instr_id == instr_id)
        res = session.execute(stmt)
        session.commit()
        return res.rowcount or 0
