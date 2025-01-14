from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from api.service.card import get_cards, handle_card_count_updates
from schemas.api.mtg_card import RequestUpdateCardCount
from schemas.api.pool import RequestCreatePool


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

async def update_number_of_cards_in_pool(tx: AsyncManagedTransaction, uid: UUID, pool_id: UUID, cards: list[RequestUpdateCardCount]):
    check_if_user_has_pool(tx, uid, pool_id)
    card_nodes = await get_cards(tx, cards)

    """ Adds or removes cards from the pool"""
    query = """
    MATCH (p:Pool {pool_id: $pool_id})
    UNWIND $cards AS card
    MATCH (c:Card {scryfall_id: card.node.scryfall_id})
    
    // Create or update the relationship between the pool and the card
    MERGE (p)-[r:CONTAINS]->(c)
    """

    # Set the quantity of the relationship
    query += handle_card_count_updates    

    response = await tx.run(query, uid=uid, pool_id=pool_id, cards=card_nodes)
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