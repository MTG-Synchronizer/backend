from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from schemas.api.card import CardInCollection, CreateSet
from utils.card import format_card_name_front

async def update_number_of_cards_in_collection(tx: AsyncManagedTransaction, uid: UUID, cards: list[CardInCollection]):
    cards = [[format_card_name_front(card.name), card.quantity] for card in cards]


    """ Adds or removes cards from the user's collection """
    query = """
    MATCH (u:User {uid: $uid})
    UNWIND $cards AS card
    MATCH (c:Card {name_front: card[0]})
    
    // Create or update the relationship between the user and the card
    MERGE (u)-[r:OWNS]->(c)

    // Set the quantity of the relationship
    ON CREATE SET r.quantity = card[1]
    ON MATCH SET r.quantity = r.quantity + card[1]

    // Use a conditional operation for deletion
    WITH c, r, r.quantity AS quantity
    FOREACH (_ IN CASE WHEN quantity <= 0 THEN [1] ELSE [] END |
        DELETE r
    )
    
    // Return the card name and the quantity
    RETURN c.name_front, CASE WHEN quantity <= 0 THEN null ELSE r.quantity END AS relationship
    """
    response = await tx.run(query, uid=uid, cards=cards)
    return await response.data()

async def check_if_user_owns_set(tx: AsyncManagedTransaction, uid: UUID, set_id: UUID) -> bool:
    """ Checks if a user owns a set """
    query = """
    MATCH (u:User {uid: $uid})-[:Has]->(s:Set {id: $set_id})
    RETURN s
    """
    response = await tx.run(query, uid=uid, set_id=set_id)
    if not bool(await response.data()):
        raise HTTPException(status_code=401, detail="User does not own set")

async def create_set(tx: AsyncManagedTransaction, uid: UUID, set: CreateSet):
    
    """ Creates a set of cards """
    query = """
    MATCH (u:User {uid: $uid})
    CREATE (s:Set {id: apoc.create.uuid(), name: $set.name, description: $set.description})
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
    check_if_user_owns_set()

    """ Deletes a set of cards """
    query = """
    MATCH (s:Set {id: $set_id})
    DETACH DELETE s
    """
    response = await tx.run(query, uid=uid, set_id=set_id)
    return await response.data()

async def add_cards_to_set(tx: AsyncManagedTransaction, uid: UUID, set_id: UUID, cards: list[str]):
    check_if_user_owns_set()

    """ Adds cards to a set """
    query = """
    MATCH (s:Set {id: $set_id})
    UNWIND $cards AS card
    MATCH (c:Card {name_front: card})
    MERGE (s)-[:Contains]->(c)
    """
    cards = [format_card_name_front(card) for card in cards]
    response = await tx.run(query, uid=uid, set_id=set_id, cards=cards)
    return await response.data()

async def get_cards_in_set(tx: AsyncManagedTransaction, uid: UUID, set_id: UUID):
    check_if_user_owns_set()

    """ Gets all the cards in a set """
    query = """
    MATCH (s:Set {id: $set_id})-[:Contains]->(c:Card)
    RETURN c
    """

    response = await tx.run(query, uid=uid, set_id=set_id)
    return await response.data()