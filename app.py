import logging
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from flask import Flask, jsonify, make_response, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("BULLETIN_DB_PATH", os.path.join(BASE_DIR, "bulletin.db"))
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

SESSION_COOKIE_NAME = "session_id"
SESSION_BYTES = 32
SESSION_LIFETIME_HOURS = 24
MAX_POST_LENGTH = 2000
MIN_PASSWORD_LENGTH = 8
MAX_EMAIL_LENGTH = 254

app = Flask(__name__)
app.logger.setLevel(logging.INFO)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def build_session_expiration() -> str:
    return (utc_now() + timedelta(hours=SESSION_LIFETIME_HOURS)).isoformat()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    if not table_exists(conn, table_name):
        return False

    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def init_db() -> None:
    """
    Initialize the database and apply safe migrations.

    This is resilient against:
    - first startup with no bulletin.db
    - older sessions table without expires_at
    - startup under Gunicorn on Render
    """
    app.logger.info("Initializing database at %s using schema %s", DB_PATH, SCHEMA_PATH)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # 1. Create base tables if they do not exist.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              user_id INTEGER PRIMARY KEY AUTOINCREMENT,
              username_email TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
              session_id TEXT PRIMARY KEY,
              user_id INTEGER NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              author_email TEXT NOT NULL,
              body TEXT NOT NULL
            )
            """
        )

        # 2. Add expires_at if the sessions table is from the older schema.
        if not column_exists(conn, "sessions", "expires_at"):
            app.logger.info("Applying migration: add expires_at to sessions")
            conn.execute("ALTER TABLE sessions ADD COLUMN expires_at TEXT")

        # 3. Backfill missing expiry values for older rows.
        conn.execute(
            """
            UPDATE sessions
            SET expires_at = ?
            WHERE expires_at IS NULL OR TRIM(expires_at) = ''
            """,
            (build_session_expiration(),),
        )

        # 4. Create indexes only after the schema is confirmed safe.
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)"
        )

        conn.commit()
    except sqlite3.Error:
        app.logger.exception("Database initialization failed during startup.")
        raise
    finally:
        conn.close()


def looks_like_email(email: str) -> bool:
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


def generate_session_id() -> str:
    return secrets.token_urlsafe(SESSION_BYTES)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_registration_input(email: str, password: str) -> Optional[str]:
    if not looks_like_email(email):
        return "Invalid email address."

    if len(email) > MAX_EMAIL_LENGTH:
        return "Email too long."

    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

    return None


def validate_post_body(body: str) -> Optional[str]:
    if not body:
        return "Post body cannot be empty."

    if len(body) > MAX_POST_LENGTH:
        return f"Post too long (max {MAX_POST_LENGTH} characters)."

    return None


def cleanup_expired_sessions(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (utc_now_iso(),))


def get_current_user():
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None

    conn = get_db()
    try:
        cleanup_expired_sessions(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT u.user_id, u.username_email
            FROM sessions s
            JOIN users u ON u.user_id = s.user_id
            WHERE s.session_id = ?
              AND s.expires_at > ?
            """,
            (session_id, utc_now_iso()),
        )
        user = cur.fetchone()
        conn.commit()
        return user
    except sqlite3.Error as exc:
        app.logger.exception("Database error while resolving current user: %s", exc)
        return None
    finally:
        conn.close()


def create_session_for_user(user_id: int) -> str:
    session_id = generate_session_id()

    conn = get_db()
    try:
        cleanup_expired_sessions(conn)
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.execute(
            """
            INSERT INTO sessions (session_id, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, user_id, utc_now_iso(), build_session_expiration()),
        )
        conn.commit()
        return session_id
    except sqlite3.Error as exc:
        app.logger.exception("Database error while creating session: %s", exc)
        raise
    finally:
        conn.close()


# Run on import so Gunicorn/Render initializes the database before handling requests.
init_db()


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok", "server_time": utc_now_iso()})


@app.get("/api/me")
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False}), 401

    return jsonify(
        {
            "authenticated": True,
            "user_id": user["user_id"],
            "email": user["username_email"],
        }
    )


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    password = data.get("password") or ""

    validation_error = validate_registration_input(email, password)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username_email = ?", (email,))
        if cur.fetchone():
            return jsonify({"error": "User already exists."}), 409

        cur.execute(
            "INSERT INTO users (username_email, password_hash) VALUES (?, ?)",
            (email, generate_password_hash(password)),
        )
        conn.commit()
        return jsonify({"message": "User registered."}), 201
    except sqlite3.IntegrityError as exc:
        app.logger.exception("Integrity error while creating user: %s", exc)
        return jsonify({"error": "User already exists."}), 409
    except sqlite3.Error as exc:
        app.logger.exception("Database error while creating user: %s", exc)
        return jsonify({"error": "Database error while creating user."}), 500
    finally:
        conn.close()


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cleanup_expired_sessions(conn)
        cur.execute(
            "SELECT user_id, username_email, password_hash FROM users WHERE username_email = ?",
            (email,),
        )
        user = cur.fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid email or password."}), 401
    except sqlite3.Error as exc:
        app.logger.exception("Database error during login: %s", exc)
        return jsonify({"error": "Database error during login."}), 500
    finally:
        conn.close()

    session_id = create_session_for_user(user["user_id"])
    response = make_response(
        jsonify({"message": "Logged in.", "email": user["username_email"]})
    )
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        samesite="Lax",
        secure=not app.debug,
        max_age=SESSION_LIFETIME_HOURS * 60 * 60,
        path="/",
    )
    
    return response


@app.post("/api/logout")
def logout():
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        conn = get_db()
        try:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        except sqlite3.Error as exc:
            app.logger.exception("Database error during logout: %s", exc)
        finally:
            conn.close()

    response = make_response(jsonify({"message": "Logged out."}))
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@app.get("/api/posts")
def get_posts():
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

    validation_error = validate_post_body(body)
    if validation_error:
        return jsonify({"error": validation_error}), 400

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

    return (
        jsonify(
            {
                "id": post_id,
                "created_at": created_at,
                "author_email": author_email,
                "body": body,
            }
        ),
        201,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)