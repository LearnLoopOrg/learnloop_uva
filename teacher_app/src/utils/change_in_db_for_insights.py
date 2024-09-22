from typing import Any
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
import os

load_dotenv()


def update_documents(users_collection: Any, old_name: str, new_name: str) -> None:
    for user in users_collection.find():
        progress = user.get("progress", {})
        # Check if the key "Embryonale ontwikkeling - College" exists in progress
        if old_name in progress:
            # Copy the content to the new key "Embryonale ontwikkeling"
            progress[new_name] = progress[old_name]
            # Remove the old key
            del progress[old_name]

            # Update the document in the collection
            users_collection.update_one(
                {"_id": user["_id"]}, {"$set": {"progress": progress}}
            )

    print(
        f"Update completed successfully. Set progress field from {old_name} to {new_name}"
    )


if __name__ == "__main__":
    COSMOS_URI = os.getenv("LL_COSMOS_URI")
    db_client = MongoClient(COSMOS_URI, tlsCAFile=certifi.where())

    db = db_client.get_database("demo")

    users_collection = db.get_collection("users")
    update_documents(
        users_collection,
    )
