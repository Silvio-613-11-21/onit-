from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class StepCreate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        description="Название шаблона шагов (необязательно)",
        examples=["Вход в МТС Линк и отключение камеры"],
    )
    steps: dict[str, Any] = Field(
        ...,
        description=(
            "Шаги инструкции в формате JSON {ключ_поиска: действие}. "
            "Ключ проверяется последовательно по [текст, id, name, тэг, class, xpath]. "
            "Значение: 'click' для клика, либо любая строка (или 'input:текст') для ввода текста."
        ),
        examples=[
            {
                "button.Button__btn___QAHvH.OdinControl__control___b1rRn": "click",
                "Войти": "click",
            }
        ],
    )


class StepUpdate(BaseModel):
    title: Optional[str] = Field(default=None, description="Новое название набора шагов")
    steps: Optional[dict[str, Any]] = Field(
        default=None, description="Новые шаги (JSON)"
    )


class StepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    steps: dict[str, Any]


StepModel = StepCreate
