import ingest.scryfall_bulk_data_injest as target
import uuid

def test_format_data():
    data = [
        {
            "oracle_id": uuid.uuid4(),
            "name": "Card 1",
            "type_line": "Creature",
        },
        {
            "oracle_id": uuid.uuid4(),
            "name": "Cärd 2 Front // çard 2 Back",
            "type_line": "Type 1 — Type 2 // Type 3",
        }
    ]

    res = target.format_data(data)

    #oracle_id test
    assert isinstance(res[0]["oracle_id"], str)
    assert isinstance(res[1]["oracle_id"], str)

    #Name Tests
    assert res[0]["name_front"] == "CARD 1"
    assert res[0]["name_back"] == None
    assert res[1]["name_front"] == "CARD 2 FRONT"
    assert res[1]["name_back"] == "CARD 2 BACK"

    #Types test
    assert res[0]["types"] == ["Creature"]
    assert res[1]["types"] == ['Type 1', 'Type 2', 'Type 3']
