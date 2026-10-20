import os
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from src.repositories.cookierep import (
    get_all_cookies,
    get_cookie_by_id,
    create_cookie,
    update_cookie,
    delete_cookie,
)
from src.models.cookiemodel import CookieCreate, CookieUpdate
from src.services.selenium_service import (
    parse_cookie_file_content,
    parse_cookie_file_to_selenium_list,
)


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


async def parse_local_cookie_file_selenium(
    file_path: str = "cookie.txt",
) -> List[Dict[str, str]]:
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл '{file_path}' не найден",
        )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_cookie_file_to_selenium_list(content)


async def parse_local_cookie_file(file_path: str = "cookie.txt") -> Dict[str, str]:
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл '{file_path}' не найден",
        )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_cookie_file_content(content)


async def create_cookie_from_file(
    title: Optional[str] = "Импорт из cookie.txt",
    file_path: str = "cookie.txt",
):
    cookies_list = await parse_local_cookie_file_selenium(file_path=file_path)
    return create_cookie(CookieCreate(title=title, cookie=cookies_list))
