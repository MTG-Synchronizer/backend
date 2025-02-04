from typing import Optional
from pydantic import BaseModel
from schemas.api.mtg_card import RequestUpdateCard

class RequestCreatePool(BaseModel):
    name: str
    description: Optional[str] = ""
    cards: Optional[list[RequestUpdateCard]] = []