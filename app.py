import sqlite3
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template

DB_PATH = "bulletin.db"

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

@app.get("/")
def home():
    return render_template("index.html")

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
    data = request.get_json(silent=True) or {}

    author_email = (data.get("author_email") or "").strip()
    body = (data.get("body") or "").strip()

    if not looks_like_email(author_email):
        return jsonify({"error": "Invalid email address."}), 400

    if not body:
        return jsonify({"error": "Post body cannot be empty."}), 400

    if len(author_email) > 254:
        return jsonify({"error": "Email too long."}), 400

    if len(body) > 2000:
        return jsonify({"error": "Post too long (max 2000 characters)."}), 400

    created_at = datetime.now(timezone.utc).isoformat()

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
        "body": body
    }), 201

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
