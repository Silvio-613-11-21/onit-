from typing import List
from typing import Optional
from typing import Any

from datetime import time
from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import CheckConstraint

from sqlalchemy import String, JSON, Integer, Time, Date, Boolean

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSON}

class Instruction(Base):
    __tablename__ = "instruction"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String)
    steps: Mapped[dict[str, Any]] = mapped_column(JSON)
    cookie: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    regular_actions:Mapped[List["RegularAction"]] = relationship(
        back_populates="instruction", cascade="all, delete-orphan"
    )

    single_actions:Mapped[List["SingleAction"]] = relationship(
        back_populates="instruction", cascade="all, delete-orphan"
    ) 

    logs: Mapped[List["Log"]] = relationship(
        back_populates="instruction",  cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Instr(id={self.id!r}, link={self.url!r}, instr={self.steps!r} , cookie={self.cookie!r} )"


class RegularAction(Base):
    __tablename__ = "regular_action"

    id: Mapped[int] = mapped_column(primary_key=True)
    instr_id:Mapped[int] = mapped_column(ForeignKey("instruction.id"))
    day:Mapped[int] = mapped_column(Integer, nullable=False)
    time_start: Mapped[time] = mapped_column(Time, nullable=False)
    time_end: Mapped[time] = mapped_column(Time, nullable=False)

    instruction: Mapped["Instruction"] = relationship(back_populates="regular_actions")

    __table_args__ = (
        CheckConstraint("day >= 0 AND day <= 6", name="ck_regular_action_day_0_6"),
        Index("ix_regular_action_day_time", "day", "time_start"),
    )

    def __repr__(self) -> str:
        return f"RegularAction(id={self.id!r}, instr_id={self.instr_id!r}, day={self.day!r}, time_start={self.time_start!r}, time_end={self.time_end!r})"

class SingleAction(Base):
    __tablename__  = "single_action"
    id: Mapped[int] = mapped_column(primary_key=True)
    instr_id:Mapped[int] = mapped_column(ForeignKey("instruction.id"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time_start: Mapped[time] = mapped_column(Time, nullable=False)
    time_end: Mapped[time] = mapped_column(Time, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    instruction: Mapped["Instruction"] = relationship(back_populates="single_actions")

    __table_args__ = (
        Index("ix_single_action_pending", "is_complete", "date", "time_start"),
    )

    def __repr__(self) -> str:
        return f"SingleAction(id={self.id!r}, instr_id={self.instr_id!r}, date={self.date!r}, time_start={self.time_start!r}, time_end={self.time_end!r}, is_complete={self.is_complete!r})"

class Log(Base):
    __tablename__ = "log"
    id: Mapped[int] = mapped_column(primary_key=True)
    instr_id:Mapped[int] = mapped_column(ForeignKey("instruction.id"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    is_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    message: Mapped[Optional[str]] = mapped_column(String) 

    instruction: Mapped["Instruction"] = relationship(back_populates="logs")

    __table_args__ = (
        Index("ix_log_instr_date", "instr_id", "date"),
    )

    def __repr__(self) -> str:
        return f"Log(id={self.id!r}, instr_id={self.instr_id!r}, date={self.date!r}, time={self.time!r}, is_success={self.is_success!r}, message={self.message!r})"