from typing import Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

CookiePayload = Union[List[dict[str, Any]], dict[str, Any]]


class CookieCreate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        description="Название набора куки (например, аккаунт или сервис)",
        examples=["Аккаунт МТС Линк"],
    )
    cookie: CookiePayload = Field(
        ...,
        description=(
            "Куки в формате массива объектов Selenium "
            "[{'name': '...', 'value': '...', 'domain': '.mts-link.ru', 'path': '/'}] "
            "или простого словаря {'name': 'value'}."
        ),
        examples=[
            [
                {
                    "name": "_ga",
                    "value": "GA1.2.118533033.1789973637",
                    "domain": ".mts-link.ru",
                    "path": "/",
                },
                {
                    "name": "access",
                    "value": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "domain": ".mts-link.ru",
                    "path": "/",
                },
            ]
        ],
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
