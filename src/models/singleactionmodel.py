from datetime import date as dt_date, time as dt_time
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SingleActionCreate(BaseModel):
    instr_id: int = Field(..., description="ID инструкции из таблицы instruction")
    date: dt_date = Field(
        ...,
        description="Дата выполнения (ГГГГ-ММ-ДД)",
        examples=["2026-10-13"],
    )
    time_start: dt_time = Field(
        ...,
        description="Время начала выполнения (ЧЧ:ММ:СС)",
        examples=["12:00:00"],
    )
    time_end: dt_time = Field(
        ...,
        description="Время окончания удержания браузера (ЧЧ:ММ:СС)",
        examples=["13:30:00"],
    )
    is_complete: bool = Field(
        default=False,
        description="Флаг завершенности инструкции",
    )


class SingleActionUpdate(BaseModel):
    instr_id: Optional[int] = Field(default=None, description="ID инструкции")
    date: Optional[dt_date] = Field(default=None, description="Дата выполнения")
    time_start: Optional[dt_time] = Field(default=None, description="Время начала")
    time_end: Optional[dt_time] = Field(default=None, description="Время окончания")
    is_complete: Optional[bool] = Field(default=None, description="Флаг завершенности")


class SingleActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instr_id: int
    date: dt_date
    time_start: dt_time
    time_end: dt_time
    is_complete: bool


SingleActionModel = SingleActionCreate
