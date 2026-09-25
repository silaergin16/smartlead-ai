import os
import sqlite3


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "transilation.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def create_lead(name, phone, message):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO leads (name, phone, message)
        VALUES (?, ?, ?)
        """,
        (name, phone, message)
    )

    connection.commit()
    lead_id = cursor.lastrowid
    connection.close()

    return lead_id


def get_leads():
    connection = get_connection()

    leads = connection.execute(
        """
        SELECT id, name, phone, message, created_at
        FROM leads
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return [dict(lead) for lead in leads]


def lead_ekle(isim, telefon, mesaj=""):
    return create_lead(isim, telefon, mesaj)


def tum_leadler():
    return [
        {
            "id": lead["id"],
            "isim": lead["name"],
            "telefon": lead["phone"],
            "mesaj": lead["message"],
            "tarih": lead["created_at"],
        }
        for lead in get_leads()
    ]
