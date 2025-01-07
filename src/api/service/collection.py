from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from schemas.api.collection import ResponseCardInCollection
from schemas.api.mtg_card import RequestUpdateCardCount
from utils.card import get_formatted_card
from api.service.card import get_cards

async def get_collection(tx: AsyncManagedTransaction, uid: UUID) -> list[ResponseCardInCollection]:
    """ Returns the user's collection """
    query = """
    MATCH (u:User {uid: $uid})-[r:Owns]->(c:Card)
    RETURN c as node, r.quantity as number_owned
    """
    response = await tx.run(query, uid=uid)
    return await response.data()


async def update_number_of_cards_in_collection(tx: AsyncManagedTransaction, uid: UUID, cards: list[RequestUpdateCardCount]) -> list[ResponseCardInCollection]:
    card_nodes = await get_cards(tx, cards)

    """ Adds or removes cards from the user's collection """
    query = """
    MATCH (u:User {uid: $uid})
    UNWIND $cards AS card
    MATCH (c:Card {scryfall_id: card.node.scryfall_id})
    
    // Create or update the relationship between the user and the card
    MERGE (u)-[r:Owns]->(c)

    // Set the quantity of the relationship
    ON CREATE SET r.quantity = card.update_amount
    ON MATCH SET r.quantity = r.quantity + card.update_amount

    // Use a conditional operation for deletion
    WITH c, r, r.quantity AS quantity
    FOREACH (_ IN CASE WHEN quantity <= 0 THEN [1] ELSE [] END |
        DELETE r
    )
    
    // Return the card scryfall id and the quantity
    RETURN 
    c as node,
    CASE WHEN quantity <= 0 THEN 0 ELSE r.quantity END AS number_owned
    """
    
    response = await tx.run(query, uid=uid, cards=card_nodes)
    return await response.data()
