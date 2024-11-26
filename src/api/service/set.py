from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from schemas.api.set import RequestCreateSet
from utils.card import format_card_name_front


async def check_if_user_owns_set(tx: AsyncManagedTransaction, uid: UUID, set_id: UUID) -> bool:
    """ Checks if a user owns a set """
    query = """
    MATCH (u:User {uid: $uid})-[:Has]->(s:Set {id: $set_id})
    RETURN s
    """
    response = await tx.run(query, uid=uid, set_id=set_id)
    if not bool(await response.data()):
        raise HTTPException(status_code=401, detail="User does not own set")

async def create_set(tx: AsyncManagedTransaction, uid: UUID, set: RequestCreateSet):
    
    """ Creates a set of cards """
    query = """
    MATCH (u:User {uid: $uid})
    CREATE (s:Set {set_id: apoc.create.uuid(), name: $set.name, description: $set.description})
    MERGE (u)-[:Owns]->(s)
    RETURN s
    """

    response = await tx.run(query, uid=uid, set=set)
    return await response.data()

async def get_sets(tx: AsyncManagedTransaction, uid: UUID):
    """ Gets all the sets that a user owns """
    query = """
    MATCH (u:User {uid: $uid})-[:Has]->(s:Set)
    RETURN s
    """
    response = await tx.run(query, uid=uid)
    return await response.data()

async def delete_set(tx: AsyncManagedTransaction, uid: UUID, set_id: UUID):
    check_if_user_owns_set(tx, uid, set_id)

    """ Deletes a set of cards """
    query = """
    MATCH (s:Set {set_id: $set_id})
    DETACH DELETE s
    """
    response = await tx.run(query, uid=uid, set_id=set_id)
    return await response.data()

async def add_cards_to_set(tx: AsyncManagedTransaction, uid: UUID, set_id: UUID, cards: list[str]):
    check_if_user_owns_set(tx, uid, set_id)

    """ Adds cards to a set """
    query = """
    MATCH (s:Set {set_id: $set_id})
    UNWIND $cards AS card
    MATCH (c:Card {name_front: card})
    MERGE (s)-[:Contains]->(c)
    """
    cards = [format_card_name_front(card) for card in cards]
    response = await tx.run(query, uid=uid, set_id=set_id, cards=cards)
    return await response.data()

async def get_cards_in_set(tx: AsyncManagedTransaction, uid: UUID, set_id: UUID):
    check_if_user_owns_set(tx, uid, set_id)

    """ Gets all the cards in a set """
    query = """
    MATCH (s:Set {set_id: $set_id})-[:Contains]->(c:Card)
    RETURN c
    """

    response = await tx.run(query, uid=uid, set_id=set_id)
    return await response.data()