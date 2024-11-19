import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from schemas.api import card as schemas
from api.routers import user as router
from api.service import user as service


@pytest.mark.asyncio
async def test_update_number_of_cards_in_collection_empty():
    # Mock the transaction object
    mock_tx = AsyncMock()
    
    # Mock the response from the transaction run
    mock_response = AsyncMock()
    mock_response.data.return_value = []
    mock_tx.run.return_value = mock_response
    
    # Define test data
    user_id = uuid4()
    cards = []
    
    # Call the function
    result = await service.update_number_of_cards_in_collection(mock_tx, user_id, cards)
    
    # Verify the result matches the mocked response
    assert result == []

@pytest.mark.asyncio
async def test_update_number_of_cards_in_collection_invalid_quantity():
    # Mock the transaction object
    mock_tx = AsyncMock()
    
    # Mock the response from the transaction run
    mock_response = AsyncMock()
    mock_response.data.return_value = [
        {"c.name_front": "Card1", "relationship": None}
    ]
    mock_tx.run.return_value = mock_response
    
    # Define test data
    user_id = uuid4()
    cards = [
        schemas.CardInCollection(name_front="Card1", quantity=-1)
    ]
    
    # Call the function
    result = await service.update_number_of_cards_in_collection(mock_tx, user_id, cards)
    
    # Verify the result matches the mocked response
    assert result == [
        {"c.name_front": "Card1", "relationship": None}
    ]