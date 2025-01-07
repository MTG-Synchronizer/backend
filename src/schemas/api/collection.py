from pydantic import BaseModel, PositiveInt
from schemas.api.mtg_card import MtgCard

class ResponseCardInCollection(BaseModel):
    node: MtgCard
    number_owned: PositiveInt