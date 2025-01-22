from pydantic import BaseModel, Field, PositiveInt, model_validator
from typing import ClassVar, List, Optional

from schemas import URLstr, UUID4str


from pydantic import BaseModel
from typing import Optional

mtg_card_legalities_list = [
    "standard",
    "future",
    "historic",
    "timeless",
    "gladiator",
    "pioneer",
    "explorer",
    "modern",
    "legacy",
    "pauper",
    "vintage",
    "penny",
    "commander",
    "oathbreaker",
    "standardbrawl",
    "brawl",
    "alchemy",
    "paupercommander",
    "duel",
    "oldschool",
    "premodern",
]

# def create_mtg_card_legalities_model(default_value: Optional[bool] = False):
#     """Dynamically generates a Pydantic model with legality fields."""
#     fields = {legality: (Optional[bool], Field(default=default_value)) for legality in mtg_card_legalities_list}
#     return type("MtgCardLegalities", (BaseModel,), {"__annotations__": {k: v[0] for k, v in fields.items()}, **fields})

# # Create the model with a default value of `False`
# MtgCardLegalities = create_mtg_card_legalities_model()

#  -----------------

class MtgCardLegalities(BaseModel):
    legality_standard: bool
    legality_future: bool
    legality_historic: bool
    legality_timeless: bool
    legality_gladiator: bool
    legality_pioneer: bool
    legality_explorer: bool
    legality_modern: bool
    legality_legacy: bool
    legality_pauper: bool
    legality_vintage: bool
    legality_penny: bool
    legality_commander: bool
    legality_oathbreaker: bool
    legality_standardbrawl: bool
    legality_brawl: bool
    legality_alchemy: bool
    legality_paupercommander: bool
    legality_duel: bool
    legality_oldschool: bool
    legality_premodern: bool

class MtgCardPrices(BaseModel):
    price_usd: Optional[float] = None
    price_usd_foil: Optional[float] = None
    price_eur: Optional[float] = None
    price_tix: Optional[float] = None

class MtgCard(MtgCardLegalities, MtgCardPrices):
    scryfall_id: UUID4str
    full_name: str
    name_front: str
    name_back: Optional[str] = None

    oracle_texts: list[str]

    total_recurrences: Optional[int] = 0

    types: List[str]

    colors: List[str]
    cmc: float
    keywords: List[str]
    rarity: str

    img_uris_small: List[URLstr]
    img_uris_normal: List[URLstr]

class RequestUpdateCard(BaseModel):
    name: Optional[str] = None
    scryfall_id: Optional[UUID4str] = None

    @model_validator(mode='after')
    def identifier_xor_check(self):
        if not ((self.name != None) != (self.scryfall_id != None)):
            raise ValueError('Either name or scryfall_id must be provided.')
        return self
    

class RequestUpdateCardCount(RequestUpdateCard):
    update_amount: Optional[int] = None
    number_owned: Optional[int] = None
    ignore_amount: Optional[bool] = False

    @model_validator(mode='after')
    def quantity_xor_check(self):
        if not self.ignore_amount:
            if not ((self.update_amount != None) != (self.number_owned != None)):
                raise ValueError('Either update_amount or number_owned must be provided.')
        return self
    
class RequestUpdateCardCountResponse(RequestUpdateCardCount):
    node: MtgCard


class ResponseCardNode(BaseModel):
    node: MtgCard


class ResponseCardInCollection(ResponseCardNode):
    number_owned: int