import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time
import requests

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8466184183:AAHRlZuZuCJTTN8ScpsH3G9jBymnHQNifgU"

AUTO_DELETE = True
AUTO_DELETE_TIME = 1200  # 20 минут

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

# ===== АДРЕС =====
def get_address(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {"User-Agent": "map-app"}
        res = requests.get(url, headers=headers).json()
        return res.get("display_name", "Адрес не найден")
    except:
        return "Адрес не найден"

# ===== ДОБАВИТЬ ТОЧКУ =====
@app.route("/add", methods=["POST"])
def add_point():
    data = request.json

    lat = data["lat"]
    lon = data["lon"]
    content = data.get("content", "")
    point_type = data.get("type", "danger")

    address = get_address(lat, lon)

    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO points (lat, lon, type, content, address, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        lat,
        lon,
        point_type,
        content,
        address,
        int(time.time())
    ))
    conn.commit()
    conn.close()

    return {"status": "ok"}

# ===== СПИСОК ТОЧЕК =====
@app.route("/points")
def get_points():
    conn = sqlite3.connect("db.db")
    c = conn.cursor()

    if AUTO_DELETE:
        limit = int(time.time()) - AUTO_DELETE_TIME
        c.execute("SELECT id, lat, lon, type FROM points WHERE timestamp > ?", (limit,))
    else:
        c.execute("SELECT id, lat, lon, type FROM points")

    rows = c.fetchall()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "lat": r[1],
            "lon": r[2],
            "type": r[3]
        }
        for r in rows
    ])

# ===== ОДНА ТОЧКА =====
@app.route("/point/<int:pid>")
def get_point(pid):
    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("SELECT content, address, timestamp FROM points WHERE id = ?", (pid,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({})

    content, address, timestamp = row

    # ===== ФОТО + ТЕКСТ =====
    if content and "|" in content:
        try:
            file_id, text = content.split("|", 1)

            file = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
            ).json()

            file_path = file["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

            return jsonify({
                "file_url": file_url,
                "content": text,
                "address": address,
                "timestamp": timestamp
            })
        except:
            pass

    # ===== ПРОСТО ФОТО =====
    if content and content.startswith("AgAC"):
        try:
            file = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={content}"
            ).json()

            file_path = file["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

            return jsonify({
                "file_url": file_url,
                "address": address,
                "timestamp": timestamp
            })
        except:
            pass

    # ===== ОБЫЧНЫЙ ТЕКСТ =====
    return jsonify({
        "content": content,
        "address": address,
        "timestamp": timestamp
    })

# ===== УДАЛЕНИЕ =====
@app.route("/delete/<int:pid>", methods=["DELETE"])
def delete_point(pid):
    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("DELETE FROM points WHERE id = ?", (pid,))
    conn.commit()
    conn.close()

    return {"status": "deleted"}

# ===== ПЕРЕКЛЮЧЕНИЕ РЕЖИМА =====
@app.route("/mode", methods=["POST"])
def set_mode():
    global AUTO_DELETE
    data = request.json
    AUTO_DELETE = data.get("auto", True)
    return {"auto_delete": AUTO_DELETE}

# ===== ЗАПУСК =====
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
