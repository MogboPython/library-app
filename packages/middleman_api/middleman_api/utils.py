
import logging
import datetime

import shortuuid
from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from middleman_api.config import initialize_database

logger = logging.getLogger(__name__)
database = initialize_database()


def generate_user_identifier() -> str:
    return f'user_{shortuuid.uuid()}'

def hash_password(password: str) -> str:
    return PasswordHasher().hash(password)

def verify_password(entered_password: str, actual_hash: str) -> bool:
    try:
        ph = PasswordHasher()
        return ph.verify(actual_hash, entered_password)
    except VerifyMismatchError:
        return False

def authenticate_user(email: str, password: str):
    user = database.users.find_one({"email": email})
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_token(*, secret: str, user_id: str, is_admin: bool, expiration: datetime.timedelta) -> str:
    payload = {
        'user_id': user_id,
        'is_admin': is_admin,
        'exp': datetime.datetime.now(datetime.UTC) + expiration,
    }

    return jwt.encode(payload, secret, algorithm='HS256')

def verify_token(token: str, secret: str) -> dict[str, str] | None:
    try:
        return jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None
