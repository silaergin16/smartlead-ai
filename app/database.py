import os
import sqlite3


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATABASE_PATH = os.path.join(
    BASE_DIR,
    "transilation.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def close_db(error=None):
    """
    Flask uygulaması kapatılırken veritabanı bağlantısını kapatır.
    Bu sürümde bağlantılar doğrudan kapatıldığı için ayrıca
    kapatılacak global bir bağlantı bulunmamaktadır.
    """
    return None


def init_db(app=None):
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

    try:
        cursor = connection.execute(
            """
            INSERT INTO leads (
                name,
                phone,
                message
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                phone,
                message
            )
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_leads():
    connection = get_connection()

    try:
        leads = connection.execute(
            """
            SELECT
                id,
                name,
                phone,
                message,
                created_at
            FROM leads
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(lead) for lead in leads]

    finally:
        connection.close()


def tum_leadler():
    """
    Lead kayıtlarını routes.py'nin beklediği
    Türkçe alan adlarıyla döndürür.
    """

    leads = get_leads()

    return [
        {
            "id": lead["id"],
            "isim": lead["name"],
            "telefon": lead["phone"],
            "mesaj": lead["message"],
            "tarih": lead["created_at"],
        }
        for lead in leads
    ]


# Eski kodlarla uyumluluk
lead_ekle = create_lead
