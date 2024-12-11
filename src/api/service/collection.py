from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from schemas.api.collection import RequestUpdateCardInCollection, ResponseCardInCollection

async def get_collection(tx: AsyncManagedTransaction, uid: UUID) -> list[ResponseCardInCollection]:
    """ Returns the user's collection """
    query = """
    MATCH (u:User {uid: $uid})-[r:Owns]->(c:Card)
    RETURN c as node, r.quantity as number_owned
    """
    response = await tx.run(query, uid=uid)
    return await response.data()


async def check_cards_exist(tx: AsyncManagedTransaction, cards: list[str]) -> None:
    """ Checks if a list of cards exist, Raise HTTPException if not """
    query = """
    UNWIND $cards AS card
    MATCH (c:Card {scryfall_id: card})
    RETURN c.scryfall_id
    """
    response = await tx.run(query, cards=cards)
    matching_cards = await response.data()
    matching_cards = [card["c.scryfall_id"] for card in matching_cards]

    missing_cards = set(cards) - set(matching_cards)

    if missing_cards:
        raise HTTPException(status_code=404, detail={"error": "Card not found", "missing_cards": list(missing_cards)})


async def update_number_of_cards_in_collection(tx: AsyncManagedTransaction, uid: UUID, cards: list[RequestUpdateCardInCollection]) -> list[ResponseCardInCollection]:
    cards = [card.model_dump() for card in cards]
    await check_cards_exist(tx, [card["scryfall_id"] for card in cards])

    """ Adds or removes cards from the user's collection """
    query = """
    MATCH (u:User {uid: $uid})
    UNWIND $cards AS card
    MATCH (c:Card {scryfall_id: card.scryfall_id})
    
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
    
    response = await tx.run(query, uid=uid, cards=cards)
    return await response.data()