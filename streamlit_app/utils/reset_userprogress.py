import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi


load_dotenv()

MONGO_URI = os.getenv('MONGO_DB')
db_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

# Access the specific database and collection
db = db_client.LearnLoop
users_collection = db.users

# Find the user document
user_doc = users_collection.find_one({"username": "flower2960"})

# Check if 'progress' field exists and delete it
if user_doc and 'progress' in user_doc:
    users_collection.update_one({"username": "flower2960"}, {"$unset": {"progress": ""}})
    print("Progress field removed.")
else:
    print("Progress field does not exist")