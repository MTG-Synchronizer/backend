from fastapi import HTTPException
from neo4j import AsyncManagedTransaction
from schemas.api.mtg_card import RequestUpdateCardCount, RequestUpdateCardCountResponse
from utils.card import get_formatted_card


async def get_cards(tx: AsyncManagedTransaction, cards: list[RequestUpdateCardCount]) -> list[RequestUpdateCardCountResponse]:
    """ Returns a list of card nodes by name or id. Raise HTTPException if any card is not found """

    dump = [card.model_dump() for card in cards]

    formatted_cards = [
        {
            "scryfall_id": card["scryfall_id"],
            "name_front": get_formatted_card(card["name"])[0] if not card["scryfall_id"] else None,
            "update_amount": card["update_amount"],
        } for card in dump
    ]

    """ Returns a list of cards by name. Raise HTTPException if any card is not found """
    query = """
    UNWIND $cards AS card
        MATCH (c:Card)
            WHERE (card.scryfall_id IS NOT NULL AND c.scryfall_id = card.scryfall_id)
            OR (card.name_front IS NOT NULL AND c.name_front = card.name_front)
    RETURN c as node
    """
    response = await tx.run(query, cards=formatted_cards)
    matching_cards = await response.data()
    
    missing_cards = []

    for card in formatted_cards:
        #add the card node to formatted_cards
        node = None
        for c in matching_cards:
            _n = c['node']
            if _n['scryfall_id'] == card["scryfall_id"] or _n["name_front"] == card["name_front"]:
                node = _n
                break
        card["node"] = node

        if not node:
            missing_cards.append(card)

    if missing_cards:
        raise HTTPException(status_code=404, detail={"error": "Card not found", "missing_cards": list(missing_cards)})
    
    return formatted_cards