# FastAPI server
import hashlib
import hmac
import hashlib
import base64
import json
from typing import Optional
from fastapi import FastAPI, Form, Cookie, Body
from fastapi.responses import Response


# Объект нашего приложения на фастапи
app = FastAPI()

SECRET_KEY = "c2c6e23e72f272279d22e0f8a667ccdaec3160e65668127d3fad55898d59dfae"
PASSWORD_SALT = "5d96b79ac59586a8187810ea42609adbf9df43a6ea20117228ef6a316e96d6a6"

def sign_data(data: str) -> str:
    # Возвращает подписанные данные data
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    username_base64, sign = username_signed.split(".")
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username


def verify_password(username: str, password: str) -> bool:
    password_hash = hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest().lower()
    stored_password_hash = users[username]["password"].lower()
    return password_hash == stored_password_hash


users = {
    "user1": {
        "name": "user11",
        "password": "a26efc04bb1296d4315eaf9dc01307220cb4ac82162dafaa77d20c70be63b047",
        "balance": 100
    },
    "user2": {
        "name": "user22",
        "password": "5c1a164f5208644e9535b7759445db27524d1ff68719ce242c6c9ebbe4b6529c",
        "balance": 200
    }
}


@app.get("/")
def index_page(username: Optional[str] = Cookie(default=None)):
    with open("templates/login.html", "r") as f:
        login_page = f.read()
    if not username:
        return Response(login_page, media_type="text/html")
    valid_username = get_username_from_signed_string(username)
    if not valid_username:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username")
        return response
    try:
        user = users[valid_username]
    except KeyError:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username")
        return response
    return Response(
        f"Hi, {users[valid_username]['name']}<br />"
        f"balance: {users[valid_username]['balance']}",
        media_type="text/html")


@app.post("/login")
def process_login_page(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "success": False,
                "message": "I don't know you"
            }),
            media_type="application/json")

    response = Response(
        json.dumps({
            "success": True,
            "message": f"Hi, {user['name']}<br />Balance: {user['balance']}"
        }),
        media_type="application/json")

    username_signed = '{}.{}'.format(base64.b64encode(username.encode()).decode(), sign_data(username))
    response.set_cookie(key="username", value=username_signed)
    return response
