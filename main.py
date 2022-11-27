import string

from django.utils.baseconv import base64
from flask import Flask, request, g
from flask_cors import CORS
import jwt, datetime, os
import psycopg2

# from flask_sqlalchemy import SQLAlchemy
server = Flask(__name__)

conn = psycopg2.connect(
    host="localhost",
    database="video-to-mp3",
    user=os.environ["DB_NAME"],
    password=os.environ["DB_PASSWORD"]
)

cursor = conn.cursor()

# server.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://docker:docker@docker/video-to-mp3"
# CORS(server)


headers = {
    'Authorization': 'Basic {}'.format(
        base64.b64encode(
            '{username}:{password}'.format(
                username=g.user['username'],
                password='')
        )
    ),
}


def createJWT(user, secret, auth):
    return jwt.encode(
        {
            "username": user,
            "exp": datetime.datetime.now(tz=datetime.datetime.utc) + datetime.timedelta(minutes=10),
            "iat": datetime.datetime.utcnow(),
            "admin": auth
        },
        secret,
        algorithm="HS256",
    )


@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    user = auth.username
    password = auth.password
    if not auth:
        return "Unauthorised", 401

    check = cursor.execute(
        """SELECT * FROM users where (name, password) name=%s, password=%s""", (user, password)
    )

    if check:
        return createJWT(user, os.environ["JWT-SECRET"], True)
    else:
        return "unauthorized", 401


@server.post("/signup")
def signup():
    data = request.json()
    name = data["name"]
    email = data["email"]
    password = data["password"]
    if name and email and password:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT, email TEXT, password TEXT);
"""
        )
        cursor.execute(
            """
            INSERT INTO users (name, email, password) values (%s, %s, %s)
            """
        )
        id = cursor.fetchone()[0]
    return {"id": id}


@server.route("/validate", method=["post"])
def validate_jwt() -> string:
    encoded_jwt = request.headers["Authorization"]

    if encoded_jwt:
        token = encoded_jwt.split(" ")[1]
        decoded_jwt = jwt.decode(token, os.environ["SECRET"], "HS256")
        return decoded_jwt

    else:
        return "Missing Header Authorization", 401



if __name__ == '__main__':
    server.run(host="0.0.0.0", port=5000)
