from typing import List
from fastapi import APIRouter, status

from src.controllers.cookiecontroller import (
    list_cookies,
    get_cookie,
    add_cookie,
    edit_cookie,
    remove_cookie,
)
from src.models.cookiemodel import CookieCreate, CookieUpdate, CookieResponse

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
