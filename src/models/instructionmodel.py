from datetime import time as dt_time
from typing import Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

CookiePayload = Union[List[dict[str, Any]], dict[str, Any]]


class InstructionCreate(BaseModel):
    url: str = Field(
        ...,
        description="URL страницы, которую должен открыть Selenium",
        examples=["https://ссылка"],
    )
    step_id: int = Field(
        ...,
        description="ID набора шагов из таблицы step",
        examples=[1],
    )
    cookie_id: Optional[int] = Field(
        default=None,
        description="ID набора куки из таблицы cookie (если куки не нужны — null)",
        examples=[1],
    )


class InstructionUpdate(BaseModel):
    url: Optional[str] = Field(default=None, description="Новый URL страницы")
    step_id: Optional[int] = Field(default=None, description="Новый ID набора шагов")
    cookie_id: Optional[int] = Field(
        default=None, description="Новый ID набора куки"
    )


class InstructionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    step_id: int
    cookie_id: Optional[int] = None
    steps: dict[str, Any] = Field(
        default_factory=dict,
        description="Шаги из привязанной записи таблицы step",
    )
    cookie: Optional[CookiePayload] = Field(
        default=None,
        description="Куки из привязанной записи таблицы cookie",
    )


class InstructionRunRequest(BaseModel):
    background: bool = Field(
        default=True,
        description="Запустить в фоновом потоке (True) или дождаться завершения в запросе (False)",
    )
    time_end: Optional[dt_time] = Field(
        default=None,
        description="Удерживать браузер открытым до указанного времени (ЧЧ:ММ:СС)",
        examples=["15:30:00"],
    )
    hold_seconds: int = Field(
        default=0,
        ge=0,
        description="Сколько секунд удерживать браузер открытым после выполнения шагов (если не задан time_end)",
    )


# Обратная совместимость со старым именем модели
Instruction = InstructionCreate
