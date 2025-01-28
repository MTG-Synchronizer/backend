def test_get_userid(client_with_auth):
    response = client_with_auth.get("/user/id")
    assert response.status_code == 200
    assert response.json() == {"id": "test_user_id"}
