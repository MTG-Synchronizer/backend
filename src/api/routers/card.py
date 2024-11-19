from fastapi import APIRouter, Depends, Request

from typing import Annotated
from config.settings import get_firebase_user_from_token, get_settings
from api.service import card as service
from schemas.api.card import CardInCollection

router = APIRouter()

#Validate request body with CardInCollection schema
@router.post("/update_number_of_cards_in_collection")
async def add_cards_to_collection(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    cards: list[CardInCollection]
):
    """adds cards to the user's collection"""
    session = request.app.session
    result = await session.execute_write(service.update_number_of_cards_in_collection, user["uid"], cards)
    return result