import os

import pymongo
from dotenv import load_dotenv
from pymongo import MongoClient


class MongoDBConnection:
    def __init__(self):
        load_dotenv()
        self.client = None
        self.db = None

    def connect_to_database(self):
        mongodb_url = os.getenv("MONGODB_URL")
        self.client = MongoClient(mongodb_url)
        self.db = self.client.user_auth_db

    def close_database_connection(self):
        if self.client:
            self.client.close()

def initialize_database():
    client = MongoClient(os.getenv("MONGODB_URL"))
    database = client.user_auth_db

    database.users.create_index([('email', pymongo.ASCENDING)], unique=True)
    return database
