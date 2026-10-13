from pydantic import BaseModel
from typing import Any, Optional

class Instruction(BaseModel):
    url:str
    steps: dict[str, Any] 
    cookie: Optional[dict[str, Any]]
