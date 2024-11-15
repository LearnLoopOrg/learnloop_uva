from pymongo import MongoClient
import os
import certifi
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def connect_db(database_name: str):
    """
    Connect to either MongoDB or CosmosDB and ping to check connection.
    """

    # in development, use CosmosDB of LearnLoop

    # in production, use CosmosDB of the UvA
    LL_COSMOS_URI = os.getenv("LL_COSMOS_URI")

    print(f"Database name: {database_name}")

    db_client = MongoClient(LL_COSMOS_URI, tlsCAFile=certifi.where())
    db = db_client.get_database(database_name)

    # Ping database to check if it's connected
    try:
        db.command("ping")
        print(f"Student app is connected to {database_name} database")
    except Exception as e:
        print(f"Error: {e}")

    return db
