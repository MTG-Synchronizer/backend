def format_card_name_front(cardName):
    cardName = cardName.upper()
    if " // " in cardName:
        return cardName.split(" // ")[0]
    return cardName