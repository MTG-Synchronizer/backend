import pytest
from unittest.mock import patch
from firebase_admin import auth
from api.main import app
from config.settings import get_firebase_user_from_token
from fastapi.testclient import TestClient

# Mock Firebase auth
@pytest.fixture(scope='module')
def firebase_mock():
    with patch.object(auth, 'verify_id_token') as mock_verify_id_token:
        yield mock_verify_id_token

@pytest.fixture
def client_with_auth(firebase_mock):
    app.dependency_overrides[get_firebase_user_from_token] = lambda: {"uid": "test_user_id"}
    with TestClient(app) as client:
        yield client
