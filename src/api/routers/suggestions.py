from fastapi import APIRouter, Depends, Query, Request
from typing import Annotated, List, Optional
from config.settings import get_firebase_user_from_token
from api.service import suggestions as service
from schemas.api.pool_suggestions import CardFilters, RequestCardSuggestions

router = APIRouter()

@router.get("/pool/{pool_id}")
async def get_card_suggestions(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)],
    pool_id: str,
    from_collection: bool = Query(True),
    max_price: Optional[float] = Query(None),
    ignore_basic_lands: bool = Query(True),
    preserve_colors: bool = Query(True),
    legalities: Optional[str] = Query('')
):
    """gets card suggestions for a pool"""
    params = RequestCardSuggestions(
        from_collection= from_collection,
        filters = CardFilters(
            max_price=max_price,
            legalities=legalities.split(',') if legalities else [],
            ignore_basic_lands=ignore_basic_lands,
            preserve_colors=preserve_colors,
        )
    )

    session = request.app.session
    result = await session.execute_read(service.get_card_suggestions, user["uid"], pool_id, params)
    return result


@router.get("/collection-clusters")
async def get_card_clusters_from_collection(
    request: Request,
    user: Annotated[dict, Depends(get_firebase_user_from_token)]
):
    """gets card clusters from user's collection"""
    session = request.app.session
    result = await session.execute_read(service.get_card_clusters_from_collection, user["uid"])
    return result