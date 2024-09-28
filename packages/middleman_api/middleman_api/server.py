import os
import logging
from datetime import timedelta

from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError

from fastapi import FastAPI, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from middleman_api.utils import (
    create_token,
    verify_token,
    hash_password,
    authenticate_user,
    generate_user_identifier,
)
from middleman_api.config import MongoDBConnection, initialize_database
from middleman_api.schema import (
    User,
    VerifyRequest,
    VerifyResponse,
    RegisterRequest,
    RegisterResponse,
    FetchUsersRequest,
    FetchUsersResponse,
    AuthenticateRequest,
    AuthenticateResponse,
)

origins = [
    "127.0.0.1:8000",
    "127.0.0.1:8001",
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ACCESS_TOKEN_EXPIRE_HOURS = timedelta(hours=24)

load_dotenv()
mongodb = MongoDBConnection()
database = initialize_database()
logger = logging.getLogger(__name__)

@app.post("/api/register", response_model=RegisterResponse)
def register(user: RegisterRequest, response: Response):
    identifier = generate_user_identifier()
    hashed_password = hash_password(user.password)

    try:
        database.users.insert_one(
            {
                'email': user.email,
                'user_id': identifier,
                'is_admin': user.is_admin,
                'last_name': user.last_name,
                'first_name': user.first_name,
                'hashed_password': hashed_password,
            }
        )
    except DuplicateKeyError:
        response.status_code = status.HTTP_409_CONFLICT
        return {"message": "email address already exists", "id":""}

    return {"message": "registration successful", "id": identifier}

@app.post("/api/login", response_model=AuthenticateResponse)
def login(form_data: AuthenticateRequest):
    user = authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_token(
            secret= os.getenv("JWT_SECRET_KEY"),
            user_id=user["user_id"],
            is_admin=user["is_admin"],
            expiration=ACCESS_TOKEN_EXPIRE_HOURS,
        )
    return {
        "message": "access token returned successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user)
    }

@app.post("/api/verify", response_model=VerifyResponse)
def verify(request: VerifyRequest):
    payload = verify_token(token=request.access_token, secret= os.getenv("JWT_SECRET_KEY"))
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="access token is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    mongodb.connect_to_database()
    user = mongodb.db.users.find_one({'user_id': payload['user_id']})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="access token is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    mongodb.close_database_connection()
    return VerifyResponse(
        message='successful verification',
        user=User(**user)
    )

@app.get('/api/fetch_users', response_model=FetchUsersResponse)
def fetch_users(request: FetchUsersRequest):
    query = {}
    page = request.page if request.page > 0 else 1
    page_size = request.page_size if request.page_size > 0 else 50

    if request.ids:
        query = {'user_id': {'$in': list(request.ids)}}
        page_size = len(request.ids)
        page = 1

    skip = (page - 1) * page_size

    mongodb.connect_to_database()
    total_users = mongodb.db.users.count_documents(query)
    user_entries = mongodb.db.users.find(query).skip(skip).limit(page_size)

    users = [
        User(
            user_id = entry['user_id'],
            email = entry['email'],
            is_admin = entry['is_admin'],
            last_name = entry['last_name'],
            first_name = entry['first_name'],
        )
        for entry in user_entries
    ]

    mongodb.close_database_connection()
    return FetchUsersResponse(
        message = "Users fetched successfully",
        users = users,
        total_users = total_users,
        current_page = page,
    )

if __name__ == "__main__":
    app.run()
