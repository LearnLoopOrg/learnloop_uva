from authlib.integrations.flask_client import OAuth
from flask import Flask, url_for, redirect
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import certifi
import string
import random
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
surf_test_env = False
# --------------------------------------------

db = db_config.connect_db(use_mongodb)

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
)


# @app.route("/")
# def login():
#     global surf_test_env
#     if surf_test_env:
#         scheme = "http"
#     else:
#         scheme = "https"

#     redirect_uri = url_for("authorize", _external=True, _scheme=scheme)
#     return auth.surfconext.authorize_redirect(redirect_uri)


@app.route("/")
def welcome():
    return """
    <h1>Welkom bij LearnLoop</h1>
    <p>Klik op de knop hieronder om in te loggen met SURFconext.</p>
    <a href="/login"><button>Inloggen met SURFconext</button></a>
    """


@app.route("/login")
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
    user = db.users.find_one({"username": user_id})
    if not user:
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

    user_id = token["userinfo"]["sub"]
    save_id_to_db(user_id)

    nonce = generate_nonce(16)
    info = get_info(user_id)

    save_info_and_nonce(user_id, info, nonce)

    # nonce = save_nonce_to_db(user_id)

    # Redirect to streamlit app
    # TODO: when logging in as a student, redirect to learnloop.datanose.nl/student and when
    # logging in as a teacher redirect to learnloop.datanose.nl/teacher
    if surf_test_env:
        url = "http://localhost:8501/"
        # if info["user_description"] == "student":
        #     url = "http://localhost:8501/"
        # elif info["user_description"] == "teacher":
        #     url = "http://localhost:8502/"
    else:
        url = "https://learnloop.datanose.nl/"
        # if info["user_description"] == "student":
        #     url = "https://learnloop-student.datanose.nl/"
        # elif info["user_description"] == "teacher":
        #     url = "https://learnloop.datanose.nl/"

    redirect_url = f"{url}student?nonce={nonce}"

    return redirect(redirect_url, code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
