from typing import Optional
from pydantic import BaseModel, PositiveInt

class RequestUpdateCardInCollection(BaseModel):
    name: str
    update_amount: int

class ResponseUpdateCardInCollection(BaseModel):
    name: str
    number_owned: PositiveInt