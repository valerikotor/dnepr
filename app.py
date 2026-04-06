import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time

# ==== Настройка Flask ====
app = Flask(__name__)
CORS(app)  # чтобы карта могла делать fetch

# ==== Инициализация базы данных ====
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
            timestamp INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==== Добавление точки ====
@app.route("/add", methods=["POST"])
def add_point():
    data = request.json
    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO points (lat, lon, type, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (data["lat"], data["lon"], data["type"], data["content"], int(time.time())))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ==== Получение всех точек (для карты) ====
@app.route("/points")
def get_points():
    now = int(time.time())
    limit = now - 1200  # показываем только последние 20 минут

    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, type FROM points WHERE timestamp > ?", (limit,))
    rows = c.fetchall()
    conn.close()

    return jsonify([{"id": r[0], "lat": r[1], "lon": r[2], "type": r[3]} for r in rows])

# ==== Получение конкретной точки (для popup) ====
@app.route("/point/<int:pid>")
def get_point(pid):
    conn = sqlite3.connect("db.db")
    c = conn.cursor()
    c.execute("SELECT content FROM points WHERE id = ?", (pid,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({"content": row[0]})
    return jsonify({})

# ==== Запуск сервера с правильным портом для Render ====
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT, debug=True)
