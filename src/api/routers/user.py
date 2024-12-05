from fastapi import APIRouter, Depends, Request

from typing import Annotated
from config.settings import get_firebase_user_from_token
from api.service import user as service

router = APIRouter()

@router.get("/id")
async def get_userid(user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    """gets the firebase connected user"""
    return {"id": user["uid"]}


@router.post("/")
async def add_user(request: Request, user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    """adds a user to the database, if the user does not already exist"""
    session = request.app.session
    result = await session.execute_write(service.add_user, user["uid"])
    return result
