from typing import List, Union

from pydantic import EmailStr, BaseModel


class User(BaseModel):
    user_id: str
    email: EmailStr
    is_admin: bool
    last_name: str
    first_name: str

class UserInDB(User):
    hashed_password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    is_admin: bool
    last_name: str
    first_name: str
    password: str

class RegisterResponse(BaseModel):
    id: str
    message: str

class AuthenticateRequest(BaseModel):
    email: str
    password: str

class AuthenticateResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    user: User

class VerifyRequest(BaseModel):
    access_token: str

class VerifyResponse(BaseModel):
    message: str
    user: User

class FetchUsersRequest(BaseModel):
    page: int
    page_size: int
    ids: Union[List[str], None] = None

class FetchUsersResponse(BaseModel):
    message: str
    total_users: int
    current_page: int
    users: List[User]
