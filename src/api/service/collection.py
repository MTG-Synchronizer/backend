from uuid import UUID
from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from schemas.api.collection import RequestUpdateCardInCollection, ResponseUpdateCardInCollection
from utils.card import format_card_name_front

async def check_cards_exist(tx: AsyncManagedTransaction, cards: list[str]) -> None:
    """ Checks if a list of cards exist, Raise HTTPException if not """
    query = """
    UNWIND $cards AS card
    MATCH (c:Card {name_front: card})
    RETURN c.name_front
    """
    response = await tx.run(query, cards=cards)
    matching_cards = await response.data()
    matching_cards = [card["c.name_front"] for card in matching_cards]
    missing_cards = [card for card in cards if card not in matching_cards]

    if missing_cards:
        raise HTTPException(status_code=404, detail={"error": "Card not found", "missing_cards": missing_cards})


async def update_number_of_cards_in_collection(tx: AsyncManagedTransaction, uid: UUID, cards: list[RequestUpdateCardInCollection]) -> list[ResponseUpdateCardInCollection]:
    cards = [[format_card_name_front(card.name), card.update_amount] for card in cards]
    await check_cards_exist(tx, [card[0] for card in cards])

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
    RETURN 
    c.name_front as name, 
    CASE WHEN quantity <= 0 THEN 0 ELSE r.quantity END AS number_owned
    """
    response = await tx.run(query, uid=uid, cards=cards)
    return await response.data()
