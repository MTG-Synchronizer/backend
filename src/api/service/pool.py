from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from api.service.card import get_cards
from schemas import UUID4str
from schemas.api.mtg_card import RequestUpdateCardCount, ResponseCardNode
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

async def add_cards_to_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, cards: list[RequestUpdateCardCount]) -> list[ResponseCardNode] :
    check_if_user_has_pool(tx, uid, pool_id)

    card_nodes = await get_cards(tx, cards)

    """ Adds or removes cards from the pool"""
    query = """
    MATCH (p:Pool {pool_id: $pool_id})
    UNWIND $cards AS card
    MATCH (c:Card {scryfall_id: card.node.scryfall_id})
    MERGE (p)-[r:CONTAINS]->(c)
    RETURN c as node
    """

    response = await tx.run(query, uid=uid, pool_id=pool_id, cards=card_nodes)
    return await response.data()

async def remove_cards_from_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, cards: list[UUID4str]) -> None:
    await check_if_user_has_pool(tx, uid, pool_id)

    """ Deletes cards from the pool """
    query = """
    MATCH (p:Pool {pool_id: $pool_id})
    UNWIND $cards AS card
    MATCH (c:Card {scryfall_id: card})
    MATCH (p)-[r:CONTAINS]->(c)
    DELETE r
    """

    await tx.run(query, uid=uid, pool_id=pool_id, cards=cards)
    return


async def get_cards_in_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID) -> list[ResponseCardNode]:
    await check_if_user_has_pool(tx, uid, pool_id)

    """ Gets all the cards in a pool """
    query = """
    MATCH (p:Pool {pool_id: $pool_id})-[:CONTAINS]->(c:Card)
    RETURN c as node
    """

    response = await tx.run(query, uid=uid, pool_id=pool_id)
    return await response.data()