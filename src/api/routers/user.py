from fastapi import APIRouter, Depends, HTTPException, Query, Request

from typing import Annotated
from config.settings import get_firebase_user_from_token, get_settings
from api.service import user as service
from schemas.user import CardInCollection
from utils.card import format_card_name_front

router = APIRouter()

@router.get("/get-id")
async def get_userid(user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    """gets the firebase connected user"""
    return {"id": user["uid"]}


@router.post("/add")
async def add_user(request: Request, user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    """adds a user to the database, if the user does not already exist"""
    session = request.app.session
    result = await session.execute_write(service.add_user, user["uid"])
    return result


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
