from pydantic import BaseModel, UUID4, AnyHttpUrl, Extra, Field
from typing import List, Optional

from pydantic import BaseModel, AnyHttpUrl, UUID4
from datetime import datetime
from typing import List, Optional

class MtgCardPrices(BaseModel):
    usd: Optional[float]
    usd_foil: Optional[float]
    eur: Optional[float]
    tix: Optional[float]

class MtgCardLegalities(BaseModel):
    standard: Optional[str]
    future:Optional[str]
    historic:Optional[str]
    timeless:Optional[str]
    gladiator:Optional[str]
    pioneer:Optional[str]
    explorer:Optional[str]
    modern:Optional[str]
    legacy:Optional[str]
    pauper:Optional[str]
    vintage:Optional[str]
    penny:Optional[str]
    commander:Optional[str]
    oathbreaker:Optional[str]
    standardbrawl:Optional[str]
    brawl:Optional[str]
    alchemy:Optional[str]
    paupercommander:Optional[str]
    duel:Optional[str]
    oldschool:Optional[str]
    premodern:Optional[str]

class MtgImageUris(BaseModel):
    art_crop: Optional[AnyHttpUrl]
    border_crop: Optional[AnyHttpUrl]
    large: Optional[AnyHttpUrl]
    normal: Optional[AnyHttpUrl]
    png: Optional[AnyHttpUrl]
    small: Optional[AnyHttpUrl]

class MtgCard(BaseModel):
    name: str
    oracle_id: Optional[UUID4]
    prices: MtgCardPrices
    colors: List[str] = Field(default_factory=list)
    cmc: float
    keywords: List[str]
    legalities: MtgCardLegalities
    rarity: str
    type_line: str

    class Config:
        extra = Extra.ignore