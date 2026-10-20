from typing import Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

CookiePayload = Union[List[dict[str, Any]], dict[str, Any]]


class CookieCreate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        description="Название набора куки (например, аккаунт или сервис)",
        examples=["Аккаунт во что нибудь"],
    )
    cookie: CookiePayload = Field(
        ...,
        description=(
            "Куки в формате массива объектов Selenium "
            "[{'name': '...', 'value': '...', 'domain': '.link.ru', 'path': '/'}] "
            "или простого словаря {'name': 'value'}."
        ),
    )


class CookieUpdate(BaseModel):
    title: Optional[str] = Field(default=None, description="Новое название набора куки")
    cookie: Optional[CookiePayload] = Field(
        default=None,
        description="Новые данные куки (список объектов или словарь ключ-значение)",
    )


class CookieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    cookie: CookiePayload


CookieModel = CookieCreate
