from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi
import streamlit as st
from utils.utils import AzureUtils

load_dotenv()


@st.cache_resource(show_spinner=False)
def connect_db(use_mongodb):
    """
    Connect to either MongoDB or CosmosDB and ping to check connection.
    """

    if not use_mongodb:
        COSMOS_URI = os.getenv("COSMOS_URI")
        db_client = MongoClient(COSMOS_URI, tlsCAFile=certifi.where())
    else:
        if st.session_state.use_keyvault:
            MONGO_URI = AzureUtils.get_secret("MONGO-URI", "lluniappkv")
        else:
            MONGO_URI = os.getenv("MONGO_URI")
        db_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

    db = db_client.demo

    # Ping database to check if it's connected
    try:
        db.command("ping")
        print("Connected to database")
    except Exception as e:
        print(f"Error: {e}")

    return db
