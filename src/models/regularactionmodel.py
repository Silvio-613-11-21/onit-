from datetime import time as dt_time
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RegularActionCreate(BaseModel):
    instr_id: int = Field(..., description="ID инструкции из таблицы instruction")
    day: int = Field(
        ...,
        ge=0,
        le=6,
        description="День недели: 0 - Понедельник, 1 - Вторник, 2 - Среда, 3 - Четверг, 4 - Пятница, 5 - Суббота, 6 - Воскресенье",
        examples=[0],
    )
    time_start: dt_time = Field(
        ...,
        description="Время начала выполнения (ЧЧ:ММ:СС)",
        examples=["09:00:00"],
    )
    time_end: dt_time = Field(
        ...,
        description="Время окончания удержания браузера (ЧЧ:ММ:СС)",
        examples=["10:30:00"],
    )


class RegularActionUpdate(BaseModel):
    instr_id: Optional[int] = Field(default=None, description="ID инструкции")
    day: Optional[int] = Field(
        default=None, ge=0, le=6, description="День недели (0..6)"
    )
    time_start: Optional[dt_time] = Field(default=None, description="Время начала")
    time_end: Optional[dt_time] = Field(default=None, description="Время окончания")


class RegularActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instr_id: int
    day: int
    time_start: dt_time
    time_end: dt_time


RegularActionModel = RegularActionCreate
