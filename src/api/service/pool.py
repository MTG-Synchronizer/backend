from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from api.service.card import get_cards
from schemas import UUID4str
from schemas.api.mtg_card import RequestUpdateCard, RequestUpdateCardCount, ResponseCardNode
from schemas.api.pool import RequestCreatePool


async def check_if_user_has_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID) -> bool:
    """ Checks if a user owns a pool """
    query = """
    MATCH (u:User {uid: $uid})-[:HAS]->(p:Pool {pool_id: $pool_id})
    RETURN p
    """
    response = await tx.run(query, uid=uid, pool_id=pool_id)
    data = await response.data()

    if not data:
        raise HTTPException(status_code=401, detail="User does not own pool")
    

async def get_pool_card_colors(tx: AsyncManagedTransaction, pool_id: UUID) -> list[str]:
    """ Gets all the colors of the cards in a pool """
    query = """
    MATCH (p:Pool {pool_id: $pool_id})-[:CONTAINS]->(c:Card)
    UNWIND c.colors AS color
    WITH DISTINCT color
    RETURN COLLECT(color) AS unique_colors
    """
    response = await tx.run(query, pool_id=pool_id)
    data = await response.data()
    return data[0]['unique_colors']

async def create_pool(tx: AsyncManagedTransaction, uid: UUID, pool: RequestCreatePool):
    """ Creates a pool of cards """
    query = """
    MATCH (u:User {uid: $uid})
    CREATE (p:Pool {pool_id: apoc.create.uuid(), name: $pool.name, description: $pool.description})
    MERGE (u)-[:HAS]->(p)
    RETURN p
    """

    response = await tx.run(query, uid=uid, pool=pool)
    data = await response.data()
    if 'cards' in pool:
        cards = [RequestUpdateCard(**card) for card in pool['cards']]
        await add_cards_to_pool(tx, uid, data[0]['p']['pool_id'], cards)
    return data[0]['p']

async def get_pools(tx: AsyncManagedTransaction, uid: UUID):
    """ Gets all the pools that a user owns """
    query = """
    MATCH (u:User {uid: $uid})-[:HAS]->(p:Pool)
    RETURN p
    """
    response = await tx.run(query, uid=uid)
    return await response.data()

async def delete_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID):
    await check_if_user_has_pool(tx, uid, pool_id)

    """ Deletes a pool of cards """
    query = """
    MATCH (p:Pool {pool_id: $pool_id})
    DETACH DELETE p
    """
    response = await tx.run(query, uid=uid, pool_id=pool_id)
    return await response.data()

async def update_cards_in_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, card_ids: list[UUID4str], merge_query=str) -> list[ResponseCardNode]:
    check_if_user_has_pool(tx, uid, pool_id)

    query = """
    MATCH (p:Pool {pool_id: $pool_id})
    UNWIND $card_ids AS card_id
    MATCH (c:Card {scryfall_id: card_id})
    """

    query += merge_query

    query += """
    RETURN c as node
    """

    response = await tx.run(query, uid=uid, pool_id=pool_id, card_ids=card_ids)
    return await response.data()

async def add_cards_to_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, cards: list[RequestUpdateCard]) -> list[ResponseCardNode] :
    card_nodes = await get_cards(tx, cards)
    card_ids = [card["node"]["scryfall_id"] for card in card_nodes]

    merge_query = """MERGE (p)-[r:CONTAINS]->(c)"""
    return await update_cards_in_pool(tx, uid, pool_id, card_ids, merge_query)

async def ignore_cards_in_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, card_ids: list[UUID4str]) -> list[ResponseCardNode]:
    merge_query = "MERGE (p)-[r:IGNORE]->(c)"
    return await update_cards_in_pool(tx, uid, pool_id, card_ids, merge_query)
    
async def remove_cards_from_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, card_ids: list[UUID4str]) -> None:
    merge_query = """
    MATCH (p)-[r:CONTAINS]->(c) 
    DELETE r
    """
    return await update_cards_in_pool(tx, uid, pool_id, card_ids, merge_query)


async def get_cards_in_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID) -> list[ResponseCardNode]:
    await check_if_user_has_pool(tx, uid, pool_id)

    """ Gets all the cards in a pool """
    query = """
    MATCH (p:Pool {pool_id: $pool_id})-[:CONTAINS]->(c:Card)
    RETURN c as node
    """

    response = await tx.run(query, uid=uid, pool_id=pool_id)
    return await response.data()