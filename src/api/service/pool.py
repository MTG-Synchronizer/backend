from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from schemas import UUID4str
from schemas.api.pool import RequestCreatePool
from utils.card import get_formatted_card


async def check_if_user_has_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID) -> bool:
    """ Checks if a user owns a pool """
    query = """
    MATCH (u:User {uid: $uid})-[:HAS]->(p:Pool {id: $pool_id})
    RETURN p
    """
    response = await tx.run(query, uid=uid, pool_id=pool_id)
    if not bool(await response.data()):
        raise HTTPException(status_code=401, detail="User does not own pool")

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
    check_if_user_has_pool(tx, uid, pool_id)

    """ Deletes a pool of cards """
    query = """
    MATCH (p:Pool {pool_id: $pool_id})
    DETACH DELETE p
    """
    response = await tx.run(query, uid=uid, pool_id=pool_id)
    return await response.data()

async def add_cards_to_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, scryfall_ids: UUID4str):
    check_if_user_has_pool(tx, uid, pool_id)

    """ Adds cards to a pool """
    query = """
    MATCH (p:Pool {pool_id: $pool_id})
    UNWIND $scryfall_ids AS scryfall_id
    MATCH (c:Card {scryfall_id: scryfall_id})
    MERGE (p)-[:CONTAINS]->(c)
    """
    response = await tx.run(query, uid=uid, pool_id=pool_id, scryfall_ids=scryfall_ids)
    return await response.data()

async def get_cards_in_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID):
    check_if_user_has_pool(tx, uid, pool_id)

    """ Gets all the cards in a pool """
    query = """
    MATCH (p:Pool {pool_id: $pool_id})-[:CONTAINS]->(c:Card)
    RETURN c
    """

    response = await tx.run(query, uid=uid, pool_id=pool_id)
    return await response.data()