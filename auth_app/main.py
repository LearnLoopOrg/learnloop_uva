from authlib.integrations.flask_client import OAuth
from flask import Flask, url_for, redirect
from dotenv import load_dotenv
import os
import argparse
import string
import random
import db_config
import requests
import datetime
import os
import pprint

from tempfile import mkdtemp
from flask import Flask, jsonify, request, render_template, url_for
from werkzeug.exceptions import Forbidden
from pylti1p3.contrib.flask import (
    FlaskOIDCLogin,
    FlaskMessageLaunch,
    FlaskRequest,
    FlaskCacheDataStorage,
)
from pylti1p3.deep_link_resource import DeepLinkResource
from pylti1p3.grade import Grade
from pylti1p3.lineitem import LineItem
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration

load_dotenv()


# --------------------------------------------
# SETTINGS for DEVELOPMENT and DEPLOYMENT

# Test before deployment by runing in docker with the following commands:
# docker build -t flask-app .
# docker run --env-file .env -p 3000:3000 flask-app

# Don't forget to re-build the image again after changing the code.

use_LL_cosmosdb = False
surf_test_env = False
# --------------------------------------------

db = db_config.connect_db(use_LL_cosmosdb)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

app = Flask("LearnLoop-LTI", template_folder="templates", static_folder="static")

config = {
    "DEBUG": True,
    "ENV": "development",
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 600,
    "SECRET_KEY": "replace-me",
    "SESSION_TYPE": "filesystem",
    "SESSION_FILE_DIR": mkdtemp(),
    "SESSION_COOKIE_NAME": "pylti1p3-flask-app-sessionid",
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SECURE": False,  # should be True in case of HTTPS usage (production)
    "SESSION_COOKIE_SAMESITE": None,  # should be 'None' in case of HTTPS usage (production)
    "DEBUG_TB_INTERCEPT_REDIRECTS": False,
}
app.config.from_mapping(config)
# cache = Cache(app)

PAGE_TITLE = "LearnLoop LTI1.3"


def get_lti_config_path():
    return os.path.join(app.root_path, "configs", "lticonfig.json")


# def get_launch_data_storage():
#     return FlaskCacheDataStorage(cache)


def get_jwk_from_public_key(key_name):
    key_path = os.path.join(app.root_path, "configs", key_name)
    f = open(key_path, "r")
    key_content = f.read()
    jwk = Registration.get_jwk(key_content)
    f.close()
    return jwk


@app.route("/jwks/", methods=["GET"])
def get_jwks():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    return jsonify({"keys": tool_conf.get_jwks()})


@app.route("/oidc", methods=["GET"])
def oidc_login():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    # launch_data_storage = get_launch_data_storage()
    # Create a Flask request
    flask_request = FlaskRequest(request)
    # Get the target link URI from the request
    target_link_uri = flask_request.get_param("target_link_uri")
    if not target_link_uri:
        return "Missing 'target_link_uri' parameter", 400

    # Initiate the OIDC Login
    # oidc_login = FlaskOIDCLogin(
    #     flask_request, tool_conf, launch_data_storage=launch_data_storage
    # )
    oidc_login = FlaskOIDCLogin(flask_request, tool_conf)
    return oidc_login.enable_check_cookies().redirect(target_link_uri)


@app.route("/launch", methods=["POST"])
def launch():
    # Laad de LTI-configuratie en start een sessie
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    flask_request = FlaskRequest(request)

    # Start de LTI launch
    message_launch = FlaskMessageLaunch(flask_request, tool_conf)

    try:
        # Valideer de launch data en haal gebruikersinformatie op
        message_launch_data = message_launch.get_launch_data()
        user_id = message_launch_data.get("sub")
        roles = message_launch_data.get(
            "https://purl.imsglobal.org/spec/lti/claim/roles", []
        )

        # Maak aangepaste redirect gebaseerd op de rol van de gebruiker
        if "Instructor" in roles:
            return redirect("https://learnloop.datanose.nl/teacher")
        else:
            return redirect("https://learnloop.datanose.nl/student")

    except Exception as e:
        return f"Launch failed: {str(e)}", 500


# @app.route("/")
# def login():
#     global surf_test_env
#     if surf_test_env:
#         scheme = "http"
#     else:
#         scheme = "https"

#     redirect_uri = url_for("authorize", _external=True, _scheme=scheme)

#     return auth.surfconext.authorize_redirect(redirect_uri)


# def save_id_to_db(user_id):
#     global db
#     user = db.users.find_one({"username": user_id})
#     if not user:
#         db.users.insert_one({"username": user_id})


# def generate_nonce(length=16):
#     """Generates a random sequence of values."""
#     characters = string.ascii_letters + string.digits
#     nonce = "".join(random.choice(characters) for _ in range(length))
#     return nonce


# def save_nonce_to_db(user_id, nonce):
#     global db
#     db.users.update_one({"username": user_id}, {"$set": {"nonce": nonce}})
#     return nonce


# def save_info_and_nonce(user_id, info, nonce):
#     global db
#     print(f"Saving nonce {nonce} for user {user_id}")
#     db.users.update_one(
#         {"username": user_id},
#         {
#             "$set": {
#                 "user_description": info["user_description"],
#                 "courses": info["courses"],
#                 "nonce": nonce,
#             }
#         },
#     )


# def save_user_info_to_db(user_id, user_info):
#     global db
#     user_info = user_info.json()
#     db.users.update_one(
#         {"username": user_id},
#         {"$set": {"userinfo": user_info, "progress": {}}},
#     )
#     return user_info


# @app.route("/auth")
# def authorize():
#     global surf_test_env
#     token = auth.surfconext.authorize_access_token()

#     userinfo_endpoint = auth.surfconext.server_metadata.get("userinfo_endpoint")

#     headers = {"Authorization": f'Bearer {token["access_token"]}'}
#     userinfo = requests.get(userinfo_endpoint, headers=headers)

#     print(f"Userinfo Response: {userinfo.json()}")

#     user_id = token["userinfo"]["sub"]
#     nonce = token["userinfo"]["nonce"]

#     save_id_to_db(user_id)
#     save_nonce_to_db(user_id, nonce)
#     user_info = save_user_info_to_db(user_id, userinfo)

#     if surf_test_env:
#         url = "http://localhost:8501/"
#     else:
#         url = "https://learnloop.datanose.nl/"

#     # Redirect a user to the teacher or student page based on their affiliation
#     if "employee" in user_info["eduperson_affiliation"]:
#         redirect_url = f"{url}teacher?nonce={nonce}"
#     else:
#         redirect_url = f"{url}student?nonce={nonce}"

#     return redirect(redirect_url, code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
