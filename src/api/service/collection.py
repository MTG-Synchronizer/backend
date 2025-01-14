from uuid import UUID
from neo4j import AsyncManagedTransaction
from schemas.api.mtg_card import RequestUpdateCardCount, ResponseCardNode
from api.service.card import get_cards, handle_card_count_updates

async def get_collection(tx: AsyncManagedTransaction, uid: UUID) -> list[ResponseCardNode]:
    """ Returns the user's collection """
    query = """
    MATCH (u:User {uid: $uid})-[r:Owns]->(c:Card)
    RETURN c as node, r.quantity as number_owned
    """
    response = await tx.run(query, uid=uid)
    return await response.data()


async def update_number_of_cards_in_collection(tx: AsyncManagedTransaction, uid: UUID, cards: list[RequestUpdateCardCount]) -> list[ResponseCardNode]:
    card_nodes = await get_cards(tx, cards)

    """ Adds or removes cards from the user's collection """
    query = """
    MATCH (u:User {uid: $uid})
    UNWIND $cards AS card
    MATCH (c:Card {scryfall_id: card.node.scryfall_id})
    
    // Create or update the relationship between the user and the card
    MERGE (u)-[r:Owns]->(c)
    """

    query += handle_card_count_updates
    
    response = await tx.run(query, uid=uid, cards=card_nodes)
    return await response.data()
