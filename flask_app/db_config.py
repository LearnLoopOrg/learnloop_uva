from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi
from pymongo.server_api import ServerApi

load_dotenv()

def connect_db(use_mongodb):
    """
    Connect to either MongoDB or CosmosDB and ping to check connection.
    """
    if not use_mongodb:
        COSMOS_URI = os.getenv('COSMOS_URI')
        db_client = MongoClient(COSMOS_URI, tlsCAFile=certifi.where())
    else:
        MONGO_URI = os.getenv('MONGO_DB')
        db_client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())

    db = db_client.LearnLoop

    # Ping database to check if it's connected
    try:
        db.command("ping")
        print("Connected to database")
    except Exception as e:
        print(f"Error: {e}")

    return db
