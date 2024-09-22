from flask import Flask, request, redirect, jsonify
from pylti1p3.tool_config import ToolConfDict
from pylti1p3.message_launch import MessageLaunch
from pylti1p3.cookie import CookieService
from pylti1p3.session import SessionService
from pylti1p3.request import Request

app = Flask(__name__)
app.secret_key = "je_geheime_sleutel"

# Configureer de LTI tool instellingen
tool_config = {
    "client_id": "JE_CLIENT_ID",
    "auth_login_url": "https://saltire.lti.tool/oidc/auth",
    "auth_token_url": "https://saltire.lti.tool/oidc/token",
    "key_set_url": "https://saltire.lti.tool/oidc/jwks",
    "private_key_file": "private.key",
    "public_key_file": "public.key",
    "deployment_ids": ["JE_DEPLOYMENT_ID"],
}
tool_conf = ToolConfDict(tool_config)


@app.route("/login/", methods=["GET"])
def login():
    # Start de OIDC login flow
    request_obj = Request(request)
    cookie_service = CookieService(request_obj)
    session_service = SessionService(request_obj)
    message_launch = MessageLaunch(
        request_obj, tool_conf, session_service, cookie_service
    )
    return message_launch.redirect()


@app.route("/launch", methods=["POST"])
def launch():
    request_obj = Request(request)
    cookie_service = CookieService(request_obj)
    session_service = SessionService(request_obj)
    message_launch = MessageLaunch(
        request_obj, tool_conf, session_service, cookie_service
    )

    # Valideer de LTI launch
    launch_data = (
        message_launch.validate_registration().validate_state().get_launch_data()
    )

    # Haal de naam van de gebruiker op uit de LTI launch
    user_name = launch_data.get("name", "Student")

    # Render de app.html template en geef de naam van de gebruiker mee
    return render_template("app.html", user_name=user_name)


@app.route("/keys/", methods=["GET"])
def keys():
    # Geef de publieke sleutel terug voor JWT validatie
    return jsonify(tool_conf.get_jwks())


if __name__ == "__main__":
    app.run(debug=True)
