import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_URL"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT NOT NULL,
                telefon TEXT NOT NULL,
                mesaj TEXT,
                tarih DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


def lead_ekle(isim: str, telefon: str, mesaj: str = "") -> int:
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO leads (isim, telefon, mesaj) VALUES (?, ?, ?)",
        (isim, telefon, mesaj)
    )
    db.commit()
    return cursor.lastrowid


def tum_leadler() -> list:
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, isim, telefon, mesaj, tarih FROM leads ORDER BY tarih DESC")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
