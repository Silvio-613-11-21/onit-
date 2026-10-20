from typing import Any, Dict
from fastapi import HTTPException, status

from src.repositories.cookierep import (
    get_all_cookies,
    get_cookie_by_id,
    create_cookie,
    update_cookie,
    delete_cookie,
)
from src.models.cookiemodel import CookieCreate, CookieUpdate


async def list_cookies():
    return await get_all_cookies()


async def get_cookie(cookie_id: int):
    cookie_obj = await get_cookie_by_id(cookie_id)
    if not cookie_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Набор куки с id={cookie_id} не найден",
        )
    return cookie_obj


async def add_cookie(data: CookieCreate):
    return create_cookie(data)


async def edit_cookie(cookie_id: int, data: CookieUpdate):
    updated = update_cookie(cookie_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Набор куки с id={cookie_id} не найден",
        )
    return updated


async def remove_cookie(cookie_id: int) -> Dict[str, Any]:
    deleted = delete_cookie(cookie_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Набор куки с id={cookie_id} не найден",
        )
    return {"status": "deleted", "id": cookie_id}
