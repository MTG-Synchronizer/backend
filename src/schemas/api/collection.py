from pydantic import BaseModel, PositiveInt
from schemas import UUID4str

class RequestUpdateCardInCollection(BaseModel):
    scryfall_id: UUID4str
    update_amount: int

class ResponseCardInCollection(BaseModel):
    scryfall_id: UUID4str
    number_owned: PositiveInt