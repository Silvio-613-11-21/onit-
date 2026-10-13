from datetime import date as dt_date, time as dt_time
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LogCreate(BaseModel):
    instr_id: int = Field(..., description="ID инструкции")
    date: Optional[dt_date] = Field(
        default=None, description="Дата записи лога (по умолчанию текущая)"
    )
    time: Optional[dt_time] = Field(
        default=None, description="Время записи лога (по умолчанию текущее)"
    )
    is_success: bool = Field(..., description="Успешно ли выполнена инструкция")
    message: Optional[str] = Field(
        default=None, description="Подробное сообщение о результате выполнения"
    )


class LogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instr_id: int
    date: dt_date
    time: dt_time
    is_success: bool
    message: Optional[str] = None


LogModel = LogCreate
