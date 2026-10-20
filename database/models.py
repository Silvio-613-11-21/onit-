from typing import List, Optional, Any, Union
from datetime import time as dt_time, date as dt_date

from sqlalchemy import (
    ForeignKey,
    Index,
    CheckConstraint,
    String,
    JSON,
    Integer,
    Time,
    Date,
    Boolean,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


CookieDataType = Union[List[dict[str, Any]], dict[str, Any]]


class Base(DeclarativeBase):
    type_annotation_map = {
        dict[str, Any]: JSON,
        CookieDataType: JSON,
    }


class Step(Base):
    """
    Таблица шаблонов шагов Selenium.
    Один набор шагов может переиспользоваться для множества разных URL.
    """

    __tablename__ = "step"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    steps: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    instructions: Mapped[List["Instruction"]] = relationship(
        back_populates="step_rel"
    )

    def __repr__(self) -> str:
        return f"Step(id={self.id!r}, title={self.title!r}, steps={self.steps!r})"


class Cookie(Base):
    """
    Таблица наборов куки.
    Поддерживает хранение в JSON как списка объектов Selenium:
    [{"name": "...", "value": "...", "domain": ".mts-link.ru", "path": "/"}]
    так и простого словаря {"name": "value"}.
    Один набор куки может переиспользоваться для множества разных URL.
    """

    __tablename__ = "cookie"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cookie: Mapped[CookieDataType] = mapped_column(JSON, nullable=False)

    instructions: Mapped[List["Instruction"]] = relationship(
        back_populates="cookie_rel"
    )

    def __repr__(self) -> str:
        return f"Cookie(id={self.id!r}, title={self.title!r})"


class Instruction(Base):
    """
    Инструкция связывает конкретный URL с набором шагов (step_id)
    и опциональным набором куки (cookie_id) без дублирования данных.
    """

    __tablename__ = "instruction"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    step_id: Mapped[int] = mapped_column(
        ForeignKey("step.id", ondelete="RESTRICT"), nullable=False
    )
    cookie_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cookie.id", ondelete="SET NULL"), nullable=True
    )

    step_rel: Mapped["Step"] = relationship(
        back_populates="instructions", lazy="joined"
    )
    cookie_rel: Mapped[Optional["Cookie"]] = relationship(
        back_populates="instructions", lazy="joined"
    )

    regular_actions: Mapped[List["RegularAction"]] = relationship(
        back_populates="instruction", cascade="all, delete-orphan"
    )

    single_actions: Mapped[List["SingleAction"]] = relationship(
        back_populates="instruction", cascade="all, delete-orphan"
    )

    logs: Mapped[List["Log"]] = relationship(
        back_populates="instruction", cascade="all, delete-orphan"
    )

    @property
    def steps(self) -> dict[str, Any]:
        return self.step_rel.steps if self.step_rel else {}

    @property
    def cookie(self) -> Optional[CookieDataType]:
        return self.cookie_rel.cookie if self.cookie_rel else None

    def __repr__(self) -> str:
        return (
            f"Instr(id={self.id!r}, url={self.url!r}, "
            f"step_id={self.step_id!r}, cookie_id={self.cookie_id!r})"
        )


class RegularAction(Base):
    __tablename__ = "regular_action"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instr_id: Mapped[int] = mapped_column(
        ForeignKey("instruction.id", ondelete="CASCADE"), nullable=False
    )
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    time_start: Mapped[dt_time] = mapped_column(Time, nullable=False)
    time_end: Mapped[dt_time] = mapped_column(Time, nullable=False)

    instruction: Mapped["Instruction"] = relationship(back_populates="regular_actions")

    __table_args__ = (
        CheckConstraint("day >= 0 AND day <= 6", name="ck_regular_action_day_0_6"),
        Index("ix_regular_action_day_time", "day", "time_start"),
    )

    def __repr__(self) -> str:
        return (
            f"RegularAction(id={self.id!r}, instr_id={self.instr_id!r}, "
            f"day={self.day!r}, time_start={self.time_start!r}, time_end={self.time_end!r})"
        )


class SingleAction(Base):
    __tablename__ = "single_action"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instr_id: Mapped[int] = mapped_column(
        ForeignKey("instruction.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[dt_date] = mapped_column(Date, nullable=False)
    time_start: Mapped[dt_time] = mapped_column(Time, nullable=False)
    time_end: Mapped[dt_time] = mapped_column(Time, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    instruction: Mapped["Instruction"] = relationship(back_populates="single_actions")

    __table_args__ = (
        Index("ix_single_action_pending", "is_complete", "date", "time_start"),
    )

    def __repr__(self) -> str:
        return (
            f"SingleAction(id={self.id!r}, instr_id={self.instr_id!r}, "
            f"date={self.date!r}, time_start={self.time_start!r}, "
            f"time_end={self.time_end!r}, is_complete={self.is_complete!r})"
        )


class Log(Base):
    __tablename__ = "log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instr_id: Mapped[int] = mapped_column(
        ForeignKey("instruction.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[dt_date] = mapped_column(Date, nullable=False)
    time: Mapped[dt_time] = mapped_column(Time, nullable=False)
    is_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    instruction: Mapped["Instruction"] = relationship(back_populates="logs")

    __table_args__ = (
        Index("ix_log_instr_date", "instr_id", "date"),
    )

    def __repr__(self) -> str:
        return (
            f"Log(id={self.id!r}, instr_id={self.instr_id!r}, "
            f"date={self.date!r}, time={self.time!r}, "
            f"is_success={self.is_success!r}, message={self.message!r})"
        )
