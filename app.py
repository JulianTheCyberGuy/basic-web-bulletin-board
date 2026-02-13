import sqlite3
from datetime import datetime, timezone
from flask import Flask, request, jsonify

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

@app.get("/")
def home():
    # Frontend comes next commit
    return "Bulletin Board API is running."

@app.get("/api/posts")
def get_posts():
    since = (request.args.get("since") or "").strip()

    conn = get_db()
    cur = conn.cursor()

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
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.post("/api/posts")
def create_post():
    data = request.get_json(silent=True) or {}
    author_email = (data.get("author_email") or "").strip()
    body = (data.get("body") or "").strip()

    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (created_at, author_email, body) VALUES (?, ?, ?)",
        (created_at, author_email, body),
    )
    conn.commit()
    post_id = cur.lastrowid
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
