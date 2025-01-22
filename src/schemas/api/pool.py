from typing import Optional
from pydantic import BaseModel

class RequestCreatePool(BaseModel):
    name: str
    description: Optional[str] = ""