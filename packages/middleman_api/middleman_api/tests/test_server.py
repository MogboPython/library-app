from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleman_api.schema import RegisterRequest

app = FastAPI()
client = TestClient(app)


def test_register_user():
    request = RegisterRequest(
        email='emma.wilson@example.com',
        password='P@ssw0rd123!',
        first_name='Emma',
        last_name='Wilson',
        is_admin=False,
    )

    response = client.post(
        "/api/register",
        json=request.model_dump(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data['message'] == 'registration successful'
    assert data['id'].startswith('user_')

def test_fetch_users():
    response = client.get(

    )
    assert response.status_code == 200
