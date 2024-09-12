from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()


def connect_db(use_LL_cosmosdb):
    """
    Connect to either MongoDB or CosmosDB and ping to check connection.
    """
    if use_LL_cosmosdb:
        COSMOS_URI = os.getenv("LL_COSMOS_URI")
    else:
        COSMOS_URI = os.getenv("COSMOS_URI")

    db_client = MongoClient(COSMOS_URI, tlsCAFile=certifi.where())

    db = db_client.UvA_KNP

    # Ping database to check if it's connected
    try:
        db.command("ping")
        print("Connected to database")
    except Exception as e:
        print(f"Error: {e}")

    return db
