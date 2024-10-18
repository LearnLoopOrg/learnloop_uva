from typing import Any
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

load_dotenv()


# @st.cache_resource(show_spinner=False)
def connect_db(MONGO_URI, database_name="UvA_KNP"):
    """
    Connect to demo database of MongoDB
    """

    db_client: MongoClient[dict[str, Any]] = MongoClient(
        MONGO_URI, tlsCAFile=certifi.where()
    )

    db = db_client.get_database(database_name)

    # Ping database to check if it's connected
    try:
        db.command("ping")
        print("Connected to database")
    except Exception as e:
        print(f"Error: {e}")

    return db
