from pydantic import BaseModel, UUID4
from typing import List, Optional

from schemas import URLstr, UUID4str

class MtgCard(BaseModel):
    scryfall_id: UUID4str
    full_name: str
    name_front: str
    name_back: Optional[str] = None

    total_recurrences: Optional[int]

    types: List[str]

    colors: List[str]
    cmc: float
    keywords: List[str]
    rarity: str

    img_uris_small: List[URLstr]
    img_uris_normal: List[URLstr]


    price_usd: float
    price_usd_foil: Optional[float] = None
    price_eur: Optional[float] = None
    price_tix: Optional[float] = None

    legality_standard: Optional[str]
    legality_future: Optional[str]
    legality_historic: Optional[str]
    legality_timeless: Optional[str]
    legality_gladiator: Optional[str]
    legality_pioneer: Optional[str]
    legality_explorer: Optional[str]
    legality_modern: Optional[str]
    legality_legacy: Optional[str]
    legality_pauper: Optional[str]
    legality_vintage: Optional[str]
    legality_penny: Optional[str]
    legality_commander: Optional[str]
    legality_oathbreaker: Optional[str]
    legality_standardbrawl: Optional[str]
    legality_brawl: Optional[str]
    legality_alchemy: Optional[str]
    legality_paupercommander: Optional[str]
    legality_duel: Optional[str]
    legality_oldschool: Optional[str]
    legality_premodern: Optional[str]