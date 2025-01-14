from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from typing import List, Optional

from schemas import URLstr, UUID4str

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
    small: URLstr
    normal: URLstr

class CardFace(BaseModel):
    image_uris: Optional[MtgImageUris] = None
    oracle_text: str

class MtgCard(BaseModel):
    name: str
    id: UUID4str
    oracle_text: Optional[str] = None
    prices: MtgCardPrices
    colors: List[str] = Field(default_factory=list)
    cmc: float
    keywords: List[str]
    legalities: MtgCardLegalities
    rarity: str
    type_line: str
    image_uris: Optional[MtgImageUris] = None
    card_faces: Optional[List[CardFace]] = None
    layout: str

    class Config:
        extra = 'ignore'


    @model_validator(mode='after')
    def validate_image_uris(self):
        if not self.image_uris and not self.card_faces:
            raise ValueError("Either 'image_uris' or 'card_faces' must be provided.")
        return self