from fastapi import APIRouter, Depends, Request

from typing import Annotated
from config.settings import get_firebase_user_from_token, get_settings
from api.service import set as service
from schemas.api.set import RequestCreateSet

router = APIRouter()


@router.post("/")
async def create_set(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    set: RequestCreateSet
):
    """Create a set"""
    session = request.app.session
    result = await session.execute_write(service.create_set, user["uid"], set.dict())
    return result

@router.post("/{set_id}/cards")
async def add_cards_to_set(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    set_id: str,
    cards: list[str]
):
    """adds cards to a set"""
    session = request.app.session
    result = await session.execute_write(service.add_cards_to_set, user["uid"], set_id, cards)
    return result

@router.get("/")
async def get_sets(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)]
):
    """gets all the sets that a user owns"""
    session = request.app.session
    result = await session.execute_read(service.get_sets, user["uid"])
    return result

@router.get("/{set_id}")
async def get_cards_in_set(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    set_id: str
):
    """gets all the cards in a set"""
    session = request.app.session
    result = await session.execute_read(service.get_cards_in_set, user["uid"], set_id)
    return result

@router.delete("/{set_id}")
async def delete_set(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    set_id: str
):
    """deletes a set of cards"""
    session = request.app.session
    result = await session.execute_write(service.delete_set, user["uid"], set_id)
    return result