from authlib.integrations.flask_client import OAuth
import certifi
from flask import Flask, url_for, redirect
from dotenv import load_dotenv
import os
import string
import random

from pymongo import MongoClient
import requests
import db_config

load_dotenv()

# --------------------------------------------
# SETTINGS for DEVELOPMENT and DEPLOYMENT

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# SET ALL TO FALSE WHEN DEPLOYING
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Test before deployment by runing in docker with the following commands:
# docker build -t flask-app .
# docker run --env-file .env -p 3000:3000 flask-app

# Don't forget to re-build the image again after changing the code.

use_mongodb = False
surf_test_env = True
# --------------------------------------------

# Connect to the database
MONGO_URI = os.getenv("MONGO_URI")
db_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

# Make authentication instance for the flask app
auth = OAuth(app)

auth.register(
    name="surfconext",
    client_id=os.getenv("SURFCONEXT_CLIENT_ID"),
    client_secret=os.getenv("SURFCONEXT_CLIENT_SECRET"),
    server_metadata_url=os.getenv("SURFCONEXT_METADATA_URL"),
    client_kwargs={"scope": "openid"},
    # TODO: Currently, this scope is not allowed.
    # client_kwargs={"scope": "openid eduPersonAffiliation"},
)


@app.route("/")
def login():
    global surf_test_env
    if surf_test_env:
        scheme = "http"
    else:
        scheme = "https"

    redirect_uri = url_for("authorize", _external=True, _scheme=scheme)
    return auth.surfconext.authorize_redirect(redirect_uri)


def save_id_to_db(user_id):
    global db
    print("user_id")
    db = db_client.demo
    print(f"Looking for user with username: {user_id}")

    user = db.users.find_one({"username": user_id})
    if user is None:
        print("Username does not exist in the database. Adding it now.")
        db.users.insert_one({"username": user_id})


def generate_nonce(length=16):
    """Generates a random sequence of values."""
    characters = string.ascii_letters + string.digits
    nonce = "".join(random.choice(characters) for _ in range(length))
    return nonce


def save_nonce_to_db(user_id):
    global db
    nonce = generate_nonce(16)
    db.users.update_one({"username": user_id}, {"$set": {"nonce": nonce}})
    return nonce


def get_info(user_id):
    def fetch_info_from_UVA(user_id):
        # TODO: make call to UVA API
        return {
            "user_description": "student",
            "courses": ["course1", "course2", "course3"],
        }

    info = fetch_info_from_UVA(user_id)
    return info


def save_info_and_nonce(user_id, info, nonce):
    global db
    db.users.update_one(
        {"username": user_id},
        {
            "$set": {
                "user_description": info["user_description"],
                "courses": info["courses"],
                "nonce": nonce,
            }
        },
    )


@app.route("/auth")
def authorize():
    global surf_test_env
    token = auth.surfconext.authorize_access_token()

    userinfo_endpoint = auth.surfconext.server_metadata.get("userinfo_endpoint")
    print(f"Userinfo Endpoint: {userinfo_endpoint}")
    headers = {"Authorization": f'Bearer {token["access_token"]}'}
    # Ik wil niet de userinfo endpoint aanroepen, maar het endpoint waar ik de claims mee kan ophalen

    userinfo_response = requests.get(userinfo_endpoint, headers=headers)

    print(f"Userinfo Response: {userinfo_response.json()}")

    # TODO: Get the affilliation of the user to check whether it's a student or a teacher
    # affiliation = userinfo_response.json()["eduPersonAffiliation"]

    user_id = token["userinfo"]["sub"]
    nonce = token["userinfo"]["nonce"]
    save_id_to_db(user_id)

    # nonce = generate_nonce(16)
    info = get_info(user_id)

    save_info_and_nonce(user_id, info, nonce)

    # nonce = save_nonce_to_db(user_id)

    # Redirect to streamlit app
    # TODO: when logging in as a student, redirect to learnloop.datanose.nl/student and when
    # logging in as a teacher redirect to learnloop.datanose.nl/teacher
    if surf_test_env:
        url = "http://localhost:8502/"
        if userinfo_response["affilliation"] == "student":
            url = "http://localhost:8501/"
        elif userinfo_response["afilliation"] == "teacher":
            url = "http://localhost:8502/"
    else:
        url = "https://learnloop.datanose.nl/"
        if userinfo_response["affilliation"] == "student":
            url = "https://learnloop.datanose.nl/"
        elif userinfo_response["afilliation"] == "teacher":
            url = "https://learnloop.datanose.nl/"

    # redirect_url = f"{url}student?nonce={nonce}"
    redirect_url = f"{url}app?nonce={nonce}"

    return redirect(redirect_url, code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
