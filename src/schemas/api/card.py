from typing import Optional
from pydantic import BaseModel

class CardInCollection(BaseModel):
    name: str
    quantity: int

class CreateSet(BaseModel):
    name: str
    description: Optional[str] = ""
    
