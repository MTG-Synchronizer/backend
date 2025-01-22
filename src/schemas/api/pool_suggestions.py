from typing import List, Literal, Optional
from pydantic import BaseModel

class CardFilters(BaseModel):
    max_price: Optional[float] = None
    legalities: List[Literal[
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
    ]]
    ignore_basic_lands: Optional[bool] = True
    preserve_colors: Optional[bool] = True

class RequestCardSuggestions(BaseModel):
    from_collection: bool
    filters: Optional[CardFilters] = None