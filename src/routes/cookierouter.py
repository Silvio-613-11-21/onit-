from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Body, Query, status

from src.controllers.cookiecontroller import (
    list_cookies,
    get_cookie,
    add_cookie,
    edit_cookie,
    remove_cookie,
    parse_local_cookie_file,
    parse_local_cookie_file_selenium,
    create_cookie_from_file,
)
from src.models.cookiemodel import CookieCreate, CookieUpdate, CookieResponse
from src.services.selenium_service import (
    parse_cookie_file_content,
    parse_cookie_file_to_selenium_list,
)

router = APIRouter(
    prefix="/cookies",
    tags=["Cookies (Наборы куки)"],
)


@router.get(
    "",
    response_model=List[CookieResponse],
    summary="Получить все наборы куки из БД",
)
async def get_cookies_route():
    return await list_cookies()


@router.get(
    "/from-file",
    summary="Спарсить локальный файл cookie.txt",
    description=(
        "Читает локальный файл cookie.txt. По умолчанию возвращает словарь {name: value}; "
        "при selenium_format=true возвращает полный список объектов [{'name', 'value', 'domain', 'path'}]."
    ),
)
async def get_cookies_from_file(
    file_path: str = Query(default="cookie.txt", description="Путь к файлу с куками"),
    selenium_format: bool = Query(
        default=False,
        description="Вернуть массив объектов [{'name', 'value', 'domain', 'path'}] (True) или словарь {'name': 'value'} (False)",
    ),
) -> Union[List[Dict[str, str]], Dict[str, str]]:
    if selenium_format:
        return await parse_local_cookie_file_selenium(file_path)
    return await parse_local_cookie_file(file_path)


@router.post(
    "/import-from-file",
    response_model=CookieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Импортировать cookie.txt и сразу сохранить в таблицу cookie в БД",
)
async def import_cookie_file_to_db(
    title: Optional[str] = Query(
        default="Импорт из cookie.txt", description="Название набора куки"
    ),
    file_path: str = Query(default="cookie.txt", description="Путь к файлу"),
):
    return await create_cookie_from_file(title=title, file_path=file_path)


@router.post(
    "/parse-text",
    summary="Преобразовать текст куки (tab-separated) в JSON",
)
async def parse_cookies_text(
    raw_text: str = Body(
        ..., media_type="text/plain", description="Строки из cookie.txt"
    ),
    selenium_format: bool = Query(
        default=True,
        description="Вернуть массив объектов [{'name', 'value', 'domain', 'path'}] (True) или словарь {'name': 'value'} (False)",
    ),
) -> Union[List[Dict[str, str]], Dict[str, str]]:
    if selenium_format:
        return parse_cookie_file_to_selenium_list(raw_text)
    return parse_cookie_file_content(raw_text)


@router.get(
    "/{cookie_id}",
    response_model=CookieResponse,
    summary="Получить набор куки по ID",
)
async def get_cookie_by_id_route(cookie_id: int):
    return await get_cookie(cookie_id)


@router.post(
    "",
    response_model=CookieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый набор куки в БД",
)
async def create_cookie_route(data: CookieCreate):
    return await add_cookie(data)


@router.put(
    "/{cookie_id}",
    response_model=CookieResponse,
    summary="Обновить набор куки по ID",
)
async def update_cookie_route(cookie_id: int, data: CookieUpdate):
    return await edit_cookie(cookie_id, data)


@router.delete(
    "/{cookie_id}",
    summary="Удалить набор куки по ID",
)
async def delete_cookie_route(cookie_id: int):
    return await remove_cookie(cookie_id)
