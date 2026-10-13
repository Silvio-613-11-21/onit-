from datetime import time
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class InstructionCreate(BaseModel):
    url: str = Field(
        ...,
        description="URL страницы, которую должен открыть Selenium",
        examples=["https://my.mts-link.ru/j/120328607/24334684457"],
    )
    steps: dict[str, Any] = Field(
        ...,
        description=(
            "Шаги инструкции в формате JSON {ключ_поиска: действие}. "
            "Ключ проверяется последовательно по [текст, id, name, тэг, class, xpath]. "
            "Значение: 'click' для клика, 'clear' для очистки, 'submit'/'enter' для отправки, "
            "'wait:N' для паузы, либо любая строка (или 'input:текст') для ввода текста."
        ),
        examples=[
            {
                "button.Button__btn___QAHvH.OdinControl__control___b1rRn": "click",
                "Войти": "click",
            }
        ],
    )
    cookie: Optional[dict[str, Any]] = Field(
        default=None,
        description="Куки в формате JSON {имя_куки: значение}",
        examples=[
            {
                "_ga": "GA1.2.118533033.1789973637",
                "access": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        ],
    )


class InstructionUpdate(BaseModel):
    url: Optional[str] = Field(default=None, description="Новый URL страницы")
    steps: Optional[dict[str, Any]] = Field(
        default=None, description="Новые шаги инструкции (JSON)"
    )
    cookie: Optional[dict[str, Any]] = Field(
        default=None, description="Новые куки (JSON ключ-значение)"
    )


class InstructionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    steps: dict[str, Any]
    cookie: Optional[dict[str, Any]] = None


class InstructionRunRequest(BaseModel):
    background: bool = Field(
        default=True,
        description="Запустить в фоновом потоке (True) или дождаться завершения в запросе (False)",
    )
    time_end: Optional[time] = Field(
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
