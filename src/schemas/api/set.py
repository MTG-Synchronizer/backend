from typing import Optional
from pydantic import BaseModel

class RequestCreateSet(BaseModel):
    name: str
    description: Optional[str] = ""
    
