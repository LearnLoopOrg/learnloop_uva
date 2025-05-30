from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()


def connect_db(use_LL_cosmosdb, database_name="UvA_KNP"):
    """
    Connect to either MongoDB or CosmosDB and ping to check connection.
    """
    # Always use LL_COSMOS_URI when this configuration is active
    COSMOS_URI = os.getenv("LL_COSMOS_URI")
    # if use_LL_cosmosdb:
    #     COSMOS_URI = os.getenv("LL_COSMOS_URI")
    # else:
    #     COSMOS_URI = os.getenv("COSMOS_URI")

    db_client = MongoClient(COSMOS_URI, tlsCAFile=certifi.where())

    db = db_client[database_name]

    # Ping database to check if it's connected
    try:
        db.command("ping")
        print(f"Connected to {database_name} database")
    except Exception as e:
        print(f"Error: {e}")

    return db
