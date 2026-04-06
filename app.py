import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time
import requests

BOT_TOKEN = "8466184183:AAHRlZuZuCJTTN8ScpsH3G9jBymnHQNifgU"

app = Flask(__name__)
CORS(app)

# ===== БАЗА =====
def init_db():
    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lon REAL,
            type TEXT,
            content TEXT,
            address TEXT,
            timestamp INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ===== ПОЛУЧЕНИЕ АДРЕСА =====
def get_address(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {"User-Agent": "map-app"}
        res = requests.get(url, headers=headers).json()

        address = res.get("display_name", "Адрес не найден")
        return address

    except:
        return "Адрес не найден"

# ===== ДОБАВЛЕНИЕ ТОЧКИ =====
@app.route("/add", methods=["POST"])
def add_point():
    data = request.json

    lat = data["lat"]
    lon = data["lon"]

    address = get_address(lat, lon)

    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO points (lat, lon, type, content, address, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        lat,
        lon,
        data["type"],
        data.get("content", ""),
        address,
        int(time.time())
    ))
    conn.commit()
    conn.close()

    return {"status": "ok"}

# ===== СПИСОК ТОЧЕК =====
@app.route("/points")
def get_points():
    now = int(time.time())
    limit = now - 1200

    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, type FROM points WHERE timestamp > ?", (limit,))
    rows = c.fetchall()
    conn.close()

    return jsonify([
        {"id": r[0], "lat": r[1], "lon": r[2], "type": r[3]}
        for r in rows
    ])

# ===== ОДНА ТОЧКА =====
@app.route("/point/<int:pid>")
def get_point(pid):
    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("SELECT content, address FROM points WHERE id = ?", (pid,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({})

    content, address = row

    # фото
    if content and content.startswith("AgAC"):
        try:
            file = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={content}"
            ).json()

            file_path = file["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

            return jsonify({
                "content": content,
                "file_url": file_url,
                "address": address
            })
        except:
            pass

    return jsonify({
        "content": content,
        "address": address
    })

# ===== ЗАПУСК =====
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
