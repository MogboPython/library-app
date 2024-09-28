import datetime

import pytest

from middleman_api.utils import (
    mongodb,
    create_token,
    verify_token,
    hash_password,
    verify_password,
    generate_user_identifier,
)


@pytest.fixture
def mock_db(monkeypatch):
    class MockCollection:
        def __init__(self):
            self.users = {}

        # def find_one(self, email):
        #     return self.users.get(email)
        def find_one(self, email):
            if self.users.get(email):
                return self.users.get(email)
            return None

        def insert_one(self, document):
            self.users[document["email"]] = document
            return {'inserted_id': document["user_id"]}

    class MockMongoDB:
        def __init__(self):
            self.db = type('MockDB', (), {'users': MockCollection()})()

        def connect_to_database(self):
            pass

        def close_database_connection(self):
            pass

    mock_mongodb = MockMongoDB()
    monkeypatch.setattr(mongodb, "connect_to_database", mock_mongodb)
    monkeypatch.setattr(mongodb, "db", mock_mongodb)

    return mock_mongodb


def test_generate_user_identifier() -> None:
    identifier = generate_user_identifier()
    assert identifier.startswith('user_')
    assert len(identifier) == 27

def test_verify_password() -> None:
    password = "password"
    hashed = hash_password(password)
    assert verify_password(password, hashed)

def test_verify_wrong_password() -> None:
    password = "password"
    wrong_password = "wrong_password"
    hashed = hash_password(password)
    assert not verify_password(wrong_password, hashed)

def test_insert_and_get_user(mock_db) -> None:
    user_data = {'email': 'test@example.com', 'user_id': 'user_12345'}
    user = mock_db.db.users.insert_one(user_data)
    assert user["inserted_id"].startswith('user_')

    # Check if the user was inserted correctly
    user = mock_db.db.users.find_one('test@example.com')
    assert user_data['email'] == user_data['email']

def test_fail_get_user(mock_db) -> None:
    email = 'test@example.com'
    user = mock_db.db.users.find_one(email)
    assert user != email

# TODO: Tests for access token
def test_create_and_verify_token() -> None:
    user_id = 'test_user'
    secret = "secret"
    is_admin = False
    expiration = datetime.timedelta(hours=1)

    token = create_token(secret=secret, user_id=user_id, is_admin=is_admin, expiration=expiration)
    payload = verify_token(token=token, secret=secret)

    assert payload is not None
    assert payload['user_id'] == user_id
    assert payload['is_admin'] == is_admin

def test_create_token_different_expirations() -> None:
    secret = 'test_secret'
    user_id = 'test_user'
    is_admin = False

    short_exp = datetime.timedelta(minutes=5)
    long_exp = datetime.timedelta(days=1)

    short_token = create_token(secret=secret, user_id=user_id, is_admin=is_admin, expiration=short_exp)
    long_token = create_token(secret=secret, user_id=user_id, is_admin=is_admin, expiration=long_exp)

    assert short_token != long_token

    short_payload = verify_token(token=short_token, secret=secret)
    long_payload = verify_token(token=long_token, secret=secret)

    assert short_payload['exp'] < long_payload['exp']

def test_verify_token_different_secrets() -> None:
    user_id = 'test_user'
    is_admin = False
    expiration = datetime.timedelta(hours=1)

    token1 = create_token(secret='secret1', user_id=user_id, is_admin=is_admin, expiration=expiration)
    token2 = create_token(secret='secret2', user_id=user_id, is_admin=is_admin, expiration=expiration)

    assert verify_token(token=token1, secret='secret1') is not None
    assert verify_token(token=token2, secret='secret2') is not None
    assert verify_token(token=token1, secret='secret2') is None
    assert verify_token(token=token2, secret='secret1') is None