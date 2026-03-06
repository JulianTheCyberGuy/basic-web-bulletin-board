import secrets
import sqlite3
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, make_response
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "bulletin.db"
SESSION_COOKIE_NAME = "session_id"
SESSION_BYTES = 32

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def looks_like_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    local, _, domain = email.partition("@")
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    return True


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_session_id() -> str:
    return secrets.token_urlsafe(SESSION_BYTES)


def get_current_user():
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT u.user_id, u.username_email
            FROM sessions s
            JOIN users u ON u.user_id = s.user_id
            WHERE s.session_id = ?
            """,
            (session_id,),
        )
        return cur.fetchone()
    finally:
        conn.close()


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/me")
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False}), 401

    return jsonify({
        "authenticated": True,
        "user_id": user["user_id"],
        "email": user["username_email"],
    })


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not looks_like_email(email):
        return jsonify({"error": "Invalid email address."}), 400

    if len(email) > 254:
        return jsonify({"error": "Email too long."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM users WHERE username_email = ?", (email,))
        if cur.fetchone():
            return jsonify({"error": "User already exists."}), 409

        cur.execute(
            "INSERT INTO users (username_email, password_hash) VALUES (?, ?)",
            (email, generate_password_hash(password)),
        )
        conn.commit()
        return jsonify({"message": "User registered."}), 201
    except sqlite3.Error:
        return jsonify({"error": "Database error while creating user."}), 500
    finally:
        conn.close()


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT user_id, username_email, password_hash FROM users WHERE username_email = ?",
            (email,),
        )
        user = cur.fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid email or password."}), 401

        session_id = generate_session_id()
        cur.execute(
            "INSERT INTO sessions (session_id, user_id, created_at) VALUES (?, ?, ?)",
            (session_id, user["user_id"], utc_now_iso()),
        )
        conn.commit()
    except sqlite3.Error:
        return jsonify({"error": "Database error during login."}), 500
    finally:
        conn.close()

    response = make_response(jsonify({
        "message": "Logged in.",
        "email": user["username_email"],
    }))
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        samesite="Lax",
        secure=False,
        max_age=60 * 60 * 24,
    )
    return response


@app.post("/api/logout")
def logout():
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        finally:
            conn.close()

    response = make_response(jsonify({"message": "Logged out."}))
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get("/api/posts")
def get_posts():
    since = (request.args.get("since") or "").strip()

    conn = get_db()
    cur = conn.cursor()

    try:
        if since:
            cur.execute(
                """
                SELECT id, created_at, author_email, body
                FROM posts
                WHERE created_at > ?
                ORDER BY created_at ASC
                """,
                (since,),
            )
        else:
            cur.execute(
                """
                SELECT id, created_at, author_email, body
                FROM posts
                ORDER BY created_at ASC
                """
            )

        rows = cur.fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.post("/api/posts")
def create_post():
    user = get_current_user()
    if not user:
        return jsonify({"error": "You must be logged in to post."}), 401

    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()

    if not body:
        return jsonify({"error": "Post body cannot be empty."}), 400

    if len(body) > 2000:
        return jsonify({"error": "Post too long (max 2000 characters)."}), 400

    created_at = utc_now_iso()
    author_email = user["username_email"]

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO posts (created_at, author_email, body) VALUES (?, ?, ?)",
            (created_at, author_email, body),
        )
        conn.commit()
        post_id = cur.lastrowid
    except sqlite3.Error:
        return jsonify({"error": "Database error while saving post."}), 500
    finally:
        conn.close()

    return jsonify({
        "id": post_id,
        "created_at": created_at,
        "author_email": author_email,
        "body": body,
    }), 201


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
