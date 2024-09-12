import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
import db_config

db = db_config.connect_db(use_mongodb=True)

# Access the specific database and collection
users_collection = db.users

# Find the user document
user_doc = users_collection.find_one({"username": "flower2960"})

# Check if 'progress' field exists and delete it
if user_doc and 'progress' in user_doc:
    users_collection.update_one({"username": "flower2960"}, {"$unset": {"progress": ""}})
    print("Progress field removed.")
else:
    print("Progress field does not exist")