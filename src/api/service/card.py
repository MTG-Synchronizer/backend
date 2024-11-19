from uuid import UUID
from neo4j import AsyncManagedTransaction

from schemas.api.card import CardInCollection
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