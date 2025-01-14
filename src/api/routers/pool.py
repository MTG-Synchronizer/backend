from fastapi import APIRouter, Depends, Request

from typing import Annotated
from config.settings import get_firebase_user_from_token, get_settings
from api.service import pool as service
from schemas import UUID4str
from schemas.api.mtg_card import RequestUpdateCardCount
from schemas.api.pool import RequestCreatePool

router = APIRouter()

@router.get("/")
async def get_pools(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)]
):
    """gets all the pools that a user owns"""
    session = request.app.session
    result = await session.execute_read(service.get_pools, user["uid"])
    return result

@router.post("/")
async def create_pool(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    pool: RequestCreatePool
):
    """Create a pool"""
    session = request.app.session
    result = await session.execute_write(service.create_pool, user["uid"], pool.dict())
    return result

@router.delete("/{pool_id}")
async def delete_pool(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    pool_id: str
):
    """deletes a pool of cards"""
    session = request.app.session
    result = await session.execute_write(service.delete_pool, user["uid"], pool_id)
    return result

@router.post("/{pool_id}/cards")
async def add_cards_to_pool(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    pool_id: str,
    cards: list[RequestUpdateCardCount]
):
    """adds cards to a pool"""
    session = request.app.session
    result = await session.execute_write(service.update_number_of_cards_in_pool, user["uid"], pool_id, cards)
    return result

@router.get("/{pool_id}/cards")
async def get_cards_in_pool(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    pool_id: str
):
    """gets all the cards in a pool"""
    session = request.app.session
    result = await session.execute_read(service.get_cards_in_pool, user["uid"], pool_id)
    return result