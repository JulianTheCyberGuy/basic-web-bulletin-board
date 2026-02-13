import sqlite3
from flask import Flask

DB_PATH = "bulletin.db"

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

@app.get("/")
def home():
    return "Bulletin Board (DB initialized)."

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
