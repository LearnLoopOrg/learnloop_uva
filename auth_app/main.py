from authlib.integrations.flask_client import OAuth
from flask import Flask, url_for, redirect
from dotenv import load_dotenv
import os
import argparse
import string
import random
import db_config
import requests

load_dotenv()


# --------------------------------------------
# THIS ARG PARSER CODE DOES NOT WORK IN DEPLOYMENT FOR SOME REASON
# SETTINGS for DEVELOPMENT and DEPLOYMENT

# Test before deployment by running in docker with the following commands:
# docker build -t flask-app .
# docker run --env-file .env -p 3000:3000 flask-app

# Don't forget to re-build the image again after changing the code.

# Define the argument parser for command-line arguments
# parser = argparse.ArgumentParser(description="Flask App Configuration")

# parser.add_argument(
#     "--surf_test_env",
#     action="store_true",
#     help="Enable Surf Test Environment",
#     default=False,
# )
# parser.add_argument(
#     "--use_LL_cosmosdb",
#     action="store_true",
#     help="Use LearnLoop instance of CosmosDB, otherwise use the UvA's",
#     default=False,
# )

# args = parser.parse_args()

# # Use the command-line arguments instead of hardcoded values
# use_LL_cosmosdb = args.use_LL_cosmosdb
# surf_test_env = args.surf_test_env

# THIS ARG PARSER CODE DOES NOT WORK IN DEPLOYMENT FOR SOME REASON
# --------------------------------------------

use_LL_cosmosdb = False
surf_test_env = False

if surf_test_env:
    print(
        f"WARNING: Development settings active: Using Surf Test Environment: {surf_test_env}"
    )
if use_LL_cosmosdb:
    print(
        f"WARNING: Development settings active: Using LearnLoop CosmosDB: {use_LL_cosmosdb}"
    )
# --------------------------------------------

db = db_config.connect_db(use_LL_cosmosdb)

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


@app.route("/surf")
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


def save_nonce_to_db(user_id, nonce):
    global db
    db.users.update_one({"username": user_id}, {"$set": {"nonce": nonce}})
    return nonce


def save_info_and_nonce(user_id, info, nonce):
    global db
    print(f"Saving nonce {nonce} for user {user_id}")
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


def save_user_info_to_db(user_id, user_info):
    global db
    user_info = user_info.json()
    db.users.update_one(
        {"username": user_id},
        {"$set": {"userinfo": user_info, "progress": {}}},
    )
    return user_info


@app.route("/")
def authorize():
    global surf_test_env
    try:
        token = auth.surfconext.authorize_access_token()
    except Exception as e:
        print(f"Error during token authorization: {e}")
        return "Bad Request: Token authorization failed", 400

    userinfo_endpoint = auth.surfconext.server_metadata.get("userinfo_endpoint")

    headers = {"Authorization": f'Bearer {token["access_token"]}'}
    userinfo = requests.get(userinfo_endpoint, headers=headers)

    if userinfo.status_code != 200:
        print(f"Error fetching userinfo: {userinfo.text}")
        return "Bad Request: Failed to fetch userinfo", 400

    print(f"Userinfo Response: {userinfo.json()}")

    user_id = token["userinfo"]["sub"]
    nonce = token["userinfo"]["nonce"]

    save_id_to_db(user_id)
    save_nonce_to_db(user_id, nonce)
    user_info = save_user_info_to_db(user_id, userinfo)

    if surf_test_env:
        url = "http://localhost:8501/"
        user_info["eduperson_affiliation"] = "student"  # For testing purposes only
    else:
        url = "https://learnloop.datanose.nl/"

    # Redirect a user to the teacher or student page based on their affiliation

    redirect_url = f"{url}?nonce={nonce}"

    print(f"\n\nRedirecting to {redirect_url}\n\n")

    return redirect(redirect_url, code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
