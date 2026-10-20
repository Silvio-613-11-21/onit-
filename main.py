import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from database.create_db import init_db
from src.routes import *
from src.services.scheduler_service import scheduler_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as exc:
        logger.warning("Не удалось инициализировать БД при старте: %s", exc)

    scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.stop()


app = FastAPI(
    title="onit",
    description=(
        "Сервис управления шаблонами шагов (`step`), профилями куки (`cookie`), "
        "инструкциями (`instruction`), регулярным (`regular_action`) и "
        "нерегулярным (`single_action`) расписанием и логами выполнения (`log`)."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(step_router)
app.include_router(cookie_router)
app.include_router(instruction_router)
app.include_router(regular_action_router)
app.include_router(single_action_router)
app.include_router(log_router)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Перенаправление на Swagger UI."""
    return RedirectResponse(url="/docs")
