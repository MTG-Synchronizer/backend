import re
import unicodedata

def get_fromatted_types(text: str) -> list[str]:
    return re.split(r' // | — ', text)

def get_formatted_card(cardName: str | None) -> list[str]:
    if not cardName:
        return [None, None]

    normalized = unicodedata.normalize('NFD', cardName)
    stripped = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    cardName = stripped.upper()

    #get name_front and name_back
    if " // " in cardName:
        return cardName.split(" // ")
    else:
        return [cardName, None]