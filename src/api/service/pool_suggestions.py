from uuid import UUID
from neo4j import AsyncManagedTransaction
from api.service.pool import check_if_user_has_pool, get_pool_card_colors
from schemas.api.pool_suggestions import RequestCardSuggestions

async def get_card_suggestions(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, params: RequestCardSuggestions):
    await check_if_user_has_pool(tx, uid, pool_id)
    
    pool_colors = []
    filter_queries = []

    base_query = """
    MATCH (p:Pool {pool_id: $pool_id})
    OPTIONAL MATCH (p:Pool) - [:CONTAINS] -> (pc:Card)
    OPTIONAL MATCH (p:Pool) - [:IGNORE] -> (ic:Card)
    OPTIONAL MATCH (u:User) - [:OWNS] -> (cc:Card)
    WHERE u.uid = $uid
    WITH COALESCE(COLLECT(DISTINCT pc), []) AS pool_cards, 
         COALESCE(COLLECT(DISTINCT cc), []) AS collection_cards, 
         COALESCE(COLLECT(DISTINCT ic), []) AS ignore_cards
    MATCH (c:Card)-[r:CONNECTED]-(b:Card)
    WHERE b IN pool_cards
      AND NOT c IN pool_cards
      AND NOT c IN ignore_cards
    """

    if params.from_collection:
        filter_queries.append("AND c IN collection_cards ")
    else:
        filter_queries.append("AND NOT c IN collection_cards ")

    if params.filters.max_price:
        filter_queries.append("AND c.price_usd <= $body.filters.max_price ")

    if params.filters.legalities:
        legality_filters = " ".join([f"AND c.legality_{legality} = True " for legality in params.filters.legalities])
        filter_queries.append(legality_filters)

    if params.filters.ignore_basic_lands:
        filter_queries.append("AND NOT c.name_front IN ['PLAINS', 'ISLAND', 'SWAMP', 'MOUNTAIN', 'FOREST'] ")

    if params.filters.preserve_colors:
        pool_colors = await get_pool_card_colors(tx, pool_id)
        filter_queries.append("""
        AND NONE(color IN c.colors WHERE NOT color IN $pool_colors)
        """)

    final_query = base_query + "".join(filter_queries) + """
        WITH c, COALESCE(SUM(r.total_recurrences), 0) AS sync_score
        RETURN c as node, sync_score
        ORDER BY sync_score DESC
        LIMIT 200
    """

    response = await tx.run(final_query, uid=uid, pool_id=pool_id, body=params.model_dump(), pool_colors=pool_colors)
    return await response.data()