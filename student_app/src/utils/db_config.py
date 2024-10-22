from pymongo import MongoClient
import os
import certifi
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


# @st.cache_resource(show_spinner=False)
def connect_db(database_name="UvA_KNP"):
    """
    Connect to either MongoDB or CosmosDB and ping to check connection.
    """

    # in development, use CosmosDB of LearnLoop
    if st.session_state.use_LL_cosmosdb:
        if st.session_state.use_keyvault:
            COSMOS_URI = AzureUtils.get_secret("LL-COSMOS-URI", "lluniappkv")
        else:
            COSMOS_URI = os.getenv("LL_COSMOS_URI")
    # in production, use CosmosDB of the UvA
    else:
        COSMOS_URI = os.getenv("COSMOS_URI")

    db_client = MongoClient(COSMOS_URI, tlsCAFile=certifi.where())
    db = db_client.get_database(database_name)

    # Ping database to check if it's connected
    try:
        db.command("ping")
        print(f"Student app is connected to {database_name} database")
    except Exception as e:
        print(f"Error: {e}")

    return db
