from fastapi import APIRouter, Depends, HTTPException, Query, Request
from neo4j import AsyncManagedTransaction
from typing import Annotated
from config.settings import get_firebase_user_from_token, get_settings

router = APIRouter()

@router.get("/get-id")
async def get_userid(user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    """gets the firebase connected user"""
    return {"id": user["uid"]}
