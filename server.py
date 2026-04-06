from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time

app = Flask(__name__)
CORS(app)


def init_db():
    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS points
                 (lat REAL, lon REAL, type TEXT, timestamp INTEGER)""")
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return "SERVER WORKING"

@app.route("/add", methods=["POST"])
def add_point():
    data = request.json

    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("INSERT INTO points VALUES (?, ?, ?, ?)",
              (data["lat"], data["lon"], data["type"], int(time.time())))
    conn.commit()
    conn.close()

    return {"status": "ok"}

@app.route("/points")
def get_points():
    now = int(time.time())
    limit = now - 1200

    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("SELECT lat, lon, type FROM points WHERE timestamp > ?", (limit,))
    rows = c.fetchall()
    conn.close()

    return jsonify([
        {"lat": r[0], "lon": r[1], "type": r[2]} for r in rows
    ])

app.run(debug=True)
