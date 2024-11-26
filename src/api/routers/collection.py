from fastapi import APIRouter, Depends, Request

from typing import Annotated
from config.settings import get_firebase_user_from_token
from api.service import collection as service
from schemas.api.collection import RequestUpdateCardInCollection, ResponseUpdateCardInCollection

router = APIRouter()



@router.post("/")
async def add_cards_to_collection(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    cards: list[RequestUpdateCardInCollection]
) -> list[ResponseUpdateCardInCollection]:
    """adds cards to the user's collection"""
    session = request.app.session
    result = await session.execute_write(service.update_number_of_cards_in_collection, user["uid"], cards)
    return result