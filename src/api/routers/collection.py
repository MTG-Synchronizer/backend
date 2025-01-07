from fastapi import APIRouter, Depends, Request

from typing import Annotated
from config.settings import get_firebase_user_from_token
from api.service import collection as service
from schemas.api.collection import ResponseCardInCollection
from schemas.api.mtg_card import RequestUpdateCardCount

router = APIRouter()


@router.get("/")
async def get_collection(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)]
) -> list[ResponseCardInCollection]:
    """returns the user's collection"""
    session = request.app.session
    result = await session.execute_read(service.get_collection, user["uid"])
    return result

@router.post("/")
async def update_cards_in_collection(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    cards: list[RequestUpdateCardCount]
) -> list[ResponseCardInCollection]:
    """updates the number of cards in the user collection"""
    session = request.app.session
    result = await session.execute_write(service.update_number_of_cards_in_collection, user["uid"], cards)
    return result