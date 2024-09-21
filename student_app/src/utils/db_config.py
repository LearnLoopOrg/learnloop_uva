from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi
import streamlit as st
from utils.utils import AzureUtils

load_dotenv()


@st.cache_resource(show_spinner=False)
def connect_db(use_LL_cosmosdb):
    """
    Connect to either MongoDB or CosmosDB and ping to check connection.
    """

    # in development, use CosmosDB of LearnLoop
    if use_LL_cosmosdb:
        if st.session_state.use_keyvault:
            COSMOS_URI = AzureUtils.get_secret("LL-COSMOS-URI", "lluniappkv")
        else:
            COSMOS_URI = os.getenv("LL_COSMOS_URI")
    # in production, use CosmosDB of the UvA
    else:
        COSMOS_URI = os.getenv("COSMOS_URI")

    db_client = MongoClient(COSMOS_URI, tlsCAFile=certifi.where())
    db = db_client.get_database("UvA_NAF")

    # Ping database to check if it's connected
    try:
        db.command("ping")
        print("Student app is connected to database")
    except Exception as e:
        print(f"Error: {e}")

    return db
