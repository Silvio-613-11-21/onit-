from fastapi import FastAPI
from pydantic import BaseModel

from src.routes.instructionrouter import router as instrrouter



app = FastAPI()

app.include_router(instrrouter)

