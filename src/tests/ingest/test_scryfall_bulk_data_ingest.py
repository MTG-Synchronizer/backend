import uuid
from ingest.scryfall_bulk_data_injest import set_faces_data, set_legalities, preprocess_card_data
from utils.card import get_formatted_card, get_fromatted_types
from schemas.api.mtg_card import mtg_card_legalities_list 
import pytest
from schemas.ingest.mtg_card import MtgCard
from unittest.mock import patch
import unittest


def test_set_faces_data():
    
    # Test case when card has image_uris and oracle_text
    card = {
        "image_uris": {"small": "small_url", "normal": "normal_url"},
        "oracle_text": "sample oracle text",
    }
    result = set_faces_data(card)
    assert result["image_uris"]["small"] == ["small_url"]
    assert result["image_uris"]["normal"] == ["normal_url"]
    assert result["oracle_texts"] == ["sample oracle text"]
    
    # Test case when card has card_faces
    card = {
        "card_faces": [
            {
                "image_uris": {"small": "small_face_url", "normal": "normal_face_url"},
                "oracle_text": "face oracle text",
            }
        ]
    }
    result = set_faces_data(card)
    assert result["image_uris"]["small"] == ["small_face_url"]
    assert result["image_uris"]["normal"] == ["normal_face_url"]
    assert result["oracle_texts"] == ["face oracle text"]
    
    # Test case when card does not have image_uris or oracle_text
    card = {
        "card_faces": [
            {
                "image_uris": {"small": "small_face_url", "normal": "normal_face_url"},
                "oracle_text": "face oracle text",
            }
        ]
    }
    result = set_faces_data(card)
    assert result["image_uris"]["small"] == ["small_face_url"]
    assert result["image_uris"]["normal"] == ["normal_face_url"]
    assert result["oracle_texts"] == ["face oracle text"]
    
    # Test case when card has no image_uris and no card_faces
    card = {}
    with pytest.raises(Exception) as excinfo:
        set_faces_data(card)
    assert str(excinfo.value) == "No image_uris found"

def test_set_legalities():
    record = {
        "legalities": {
            "standard": "legal",
            "commander": "not_legal",
            "future": "not_legal",
            "historic": "legal",
            "timeless": "not_legal",
            "gladiator": "legal",
            "pioneer": "legal",
            "explorer": "legal",
            "modern": "not_legal",
            "legacy": "legal",
            "pauper": "not_legal",
            "vintage": "not_legal",
            "penny": "legal",
            "oathbreaker": "not_legal",
            "standardbrawl": "not_legal",
            "brawl": "not_legal",
            "alchemy": "legal",
            "paupercommander": "not_legal",
            "duel": "not_legal",
            "oldschool": "not_legal",
            "premodern": "not_legal",
        }
    }
    
    result = set_legalities(record)
    assert result["standard"] is True
    assert result["future"] is False
    assert result["historic"] is True
    assert result["timeless"] is False
    assert result["gladiator"] is True
    assert result["pioneer"] is True
    assert result["explorer"] is True
    assert result["modern"] is False
    assert result["legacy"] is True
    assert result["pauper"] is False
    assert result["vintage"] is False
    assert result["penny"] is True
    assert result["commander"] is False
    assert result["oathbreaker"] is False
    assert result["standardbrawl"] is False
    assert result["brawl"] is False
    assert result["alchemy"] is True
    assert result["paupercommander"] is False
    assert result["duel"] is False
    assert result["oldschool"] is False
    assert result["premodern"] is False


sample_data = [
    {
        'layout': 'normal',
        'name': 'Sample Card',
        'type_line': 'Creature',
        'legalities': {}
    },
    {
        'layout': 'art_series',
        'name': 'Art Card',
        'type_line': 'Creature',
        'legalities': {}
    }
]