from pydantic import BaseModel, field_validator

from utils.card import format_card_name_front


class CardInCollection(BaseModel):
    name: str
    quantity: int