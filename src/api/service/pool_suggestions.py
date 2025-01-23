from uuid import UUID
from neo4j import AsyncManagedTransaction
from api.service.pool import check_if_user_has_pool, get_pool_card_colors
from schemas.api.pool_suggestions import RequestCardSuggestions

async def get_card_suggestions(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, params:RequestCardSuggestions):
    await check_if_user_has_pool(tx, uid, pool_id)

    pool_colors = []
    
    query = """
    MATCH (p:Pool {pool_id: $pool_id})
    MATCH (p:Pool) - [:CONTAINS] -> (pc:Card)
    MATCH (p:Pool) - [:IGNORE] -> (ic:Card)

    MATCH (u:User) - [:OWNS] -> (cc:Card)
    WHERE u.uid = $uid

    WITH COLLECT(pc) AS pool_cards, COLLECT(cc) AS collection_cards, COLLECT(ic) AS ignore_cards

    // Match all connected cards
    MATCH (c:Card)-[r:CONNECTED]-(:Card)
    WHERE NOT c IN pool_cards
    AND NOT c IN ignore_cards
    """

    if params.from_collection:
        query += "AND c IN collection_cards "
    else:
        query += "AND NOT c IN collection_cards "

    if params.filters.max_price:
        query += "AND c.price_usd <= $body.filters.max_price "

    if params.filters.legalities:
        for legality in params.filters.legalities:
            query += f"AND c.legality_{legality} = True "

    if params.filters.ignore_basic_lands:
        query += "AND NOT c.name_front IN ['PLAINS', 'ISLAND', 'SWAMP', 'MOUNTAIN', 'FOREST'] "

    if params.filters.preserve_colors:
        pool_colors = await get_pool_card_colors(tx, pool_id)
        query += """
        // Filter out cards that are not in the pool colors
        AND NONE(color IN c.colors WHERE NOT color IN $pool_colors)
        """

    query += """
        WITH c, COALESCE(SUM(r.dynamicWeight), 0) AS totalWeight
        RETURN c as node, totalWeight as sync_score
        ORDER BY totalWeight DESC
        LIMIT 200
    """

    response = await tx.run(query, uid=uid, pool_id=pool_id, body=params.model_dump(), pool_colors=pool_colors)
    return await response.data()
