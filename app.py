import sqlite3
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template

DB_PATH = "bulletin.db"

app = Flask(__name__)

# Database helpers
def get_db() -> sqlite3.Connection:
    """Return a SQLite connection with Row access and FK enforcement enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        with open("schema.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()

def looks_like_email(email: str) -> bool:
    """Basic email validation suitable for this assignment."""
    if not email or "@" not in email:
        return False

    local, _, domain = email.partition("@")
    if not local or not domain:
        return False

    if "." not in domain:
        return False

    if domain.startswith(".") or domain.endswith("."):
        return False

    return True

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/posts")
def get_posts():
    """
    Return posts ordered by creation time.

    Time Complexity: O(n) for returning n selected rows.
    The since filter avoids re-sending old rows during polling.
    """
    since = (request.args.get("since") or "").strip()

    conn = get_db()
    try:
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
        return jsonify([dict(r) for r in rows])
    except sqlite3.Error as exc:
        app.logger.exception("Database error while fetching posts: %s", exc)
        return jsonify({"error": "Database error while fetching posts."}), 500
    finally:
        conn.close()


@app.post("/api/posts")
def create_post():
    user = get_current_user()
    if not user:
        return jsonify({"error": "You must be logged in to post."}), 401

    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()

    if not looks_like_email(author_email):
        return jsonify({"error": "Invalid email address."}), 400

    if not body:
        return jsonify({"error": "Post body cannot be empty."}), 400

    if len(author_email) > 254:
        return jsonify({"error": "Email too long."}), 400

    if len(body) > 2000:
        return jsonify({"error": "Post too long (max 2000 characters)."}), 400

    created_at = utc_now_iso()
    author_email = user["username_email"]

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO posts (created_at, author_email, body) VALUES (?, ?, ?)",
            (created_at, author_email, body),
        )
        conn.commit()
        post_id = cur.lastrowid
    except sqlite3.Error as exc:
        app.logger.exception("Database error while saving post: %s", exc)
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
