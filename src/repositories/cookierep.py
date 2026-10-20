from typing import List, Optional
from sqlalchemy import select

from database.create_db import SessionLocal
from database.models import Cookie as CookieORM
from src.models.cookiemodel import CookieCreate, CookieUpdate


async def get_all_cookies() -> List[CookieORM]:
    with SessionLocal() as session:
        res = session.execute(select(CookieORM).order_by(CookieORM.id))
        return list(res.scalars().all())


async def get_cookie_by_id(cookie_id: int) -> Optional[CookieORM]:
    with SessionLocal() as session:
        return session.get(CookieORM, cookie_id)


def create_cookie(data: CookieCreate) -> CookieORM:
    with SessionLocal() as session:
        db_cookie = CookieORM(
            title=data.title,
            cookie=data.cookie,
        )
        session.add(db_cookie)
        session.commit()
        session.refresh(db_cookie)
        return db_cookie


def update_cookie(cookie_id: int, data: CookieUpdate) -> Optional[CookieORM]:
    with SessionLocal() as session:
        db_cookie = session.get(CookieORM, cookie_id)
        if not db_cookie:
            return None

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(db_cookie, field, value)

        session.commit()
        session.refresh(db_cookie)
        return db_cookie


def delete_cookie(cookie_id: int) -> bool:
    with SessionLocal() as session:
        db_cookie = session.get(CookieORM, cookie_id)
        if not db_cookie:
            return False
        session.delete(db_cookie)
        session.commit()
        return True
