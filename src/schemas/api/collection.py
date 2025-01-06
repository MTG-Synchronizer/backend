from pydantic import BaseModel, PositiveInt
from schemas import UUID4str
from schemas.api.mtg_card import MtgCard

class RequestUpdateCardInCollection(BaseModel):
    name: str
    update_amount: int

class ResponseCardInCollection(BaseModel):
    node: MtgCard
    number_owned: PositiveInt