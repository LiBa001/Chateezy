from quart import Quart, websocket, render_template, request, session, redirect, url_for, jsonify
import uuid
import asyncio
from functools import wraps
from dataclasses import dataclass
import json
import secrets

app = Quart(__name__)
app.secret_key = secrets.token_hex()

connected_websockets = set()
connected_users = set()


@dataclass()
class User:
    uuid: str
    username: str

    def __hash__(self):
        return hash(self.uuid)

    @property
    def json(self):
        return {"uuid": self.uuid, "username": self.username}

    @staticmethod
    def from_ctx():
        return User(session["uuid"], session["username"])


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global connected_websockets
        queue = asyncio.Queue()
        connected_websockets.add(queue)
        try:
            return await func(queue, *args, **kwargs)
        finally:
            connected_websockets.remove(queue)
    return wrapper


async def broadcast(message):
    for queue in connected_websockets:
        await queue.put(message)


@app.route("/")
async def index():
    return await render_template("index.html")


@app.route("/chat", methods=["GET", "POST"])
async def chat():
    if request.method == "GET":
        if (user_id := session.get("uuid")) is None:
            return redirect(url_for("index"))

    else:
        data = await request.form
        username = data["username"]
        if len(username) > 16:
            return "fuck you", 400
        else:
            session["username"] = username

        if (user_id := session.get("uuid")) is None:
            user_id = uuid.uuid4().hex
            session["uuid"] = user_id

    user = User.from_ctx()

    if user in connected_users:
        return "already connected in another window", 409
    
    return await render_template("chat.html", username=user.username, users=list(connected_users))


@app.websocket('/ws')
@collect_websocket
async def ws(queue):
    user = User.from_ctx()
    connected_users.add(user)
    await broadcast(json.dumps({"type": "join", "user": user.json}))
    try:
        while True:
            data = await queue.get()
            await websocket.send(data)
    except asyncio.CancelledError:
        await broadcast(json.dumps({"type": "leave", "user": user.json}))
    finally:
        connected_users.remove(user)


@app.route("/chat/send", methods=["POST"])
async def send():
    data = await request.json
    author = User.from_ctx()
    
    await broadcast(json.dumps({"type": "message", "msg": data["msg"], "author": author.json}))
    return "OK"


@app.route("/chat/users")
async def get_users():
    return jsonify({"users": [user.json for user in connected_users]})


@app.route("/chat/@me")
async def get_current_user():
    return jsonify(User.from_ctx().json)


if __name__ == "__main__":
    app.run("0.0.0.0", 80, debug=True)
