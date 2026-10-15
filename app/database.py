
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
    Veritabanı bağlantıları işlem sonunda kapatıldığı
    için ayrıca kapatılacak global bağlantı yoktur.
    """
    return None


def init_db(app=None):
    """
    Tablo yoksa oluşturur.
    Eski veritabanlarında email sütunu yoksa ekler.
    Mevcut müşteri kayıtlarını silmez.
    """
    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        columns = connection.execute(
            "PRAGMA table_info(leads)"
        ).fetchall()

        column_names = [
            column["name"] for column in columns
        ]

        if "email" not in column_names:
            connection.execute(
                "ALTER TABLE leads ADD COLUMN email TEXT"
            )

        connection.commit()

    finally:
        connection.close()


def create_lead(name, phone, message, email=None):
    """
    Yeni müşteri adayını isim, telefon, mesaj ve
    e-posta bilgileriyle kaydeder.
    """
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO leads (
                name,
                phone,
                message,
                email
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                phone,
                message,
                email
            )
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_leads():
    """
    Müşteri adaylarını en yeniden en eskiye sıralar.
    """
    connection = get_connection()

    try:
        leads = connection.execute(
            """
            SELECT
                id,
                name,
                phone,
                message,
                email,
                created_at
            FROM leads
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [
            dict(lead) for lead in leads
        ]

    finally:
        connection.close()


def tum_leadler():
    """
    Kayıtları routes.py dosyasının beklediği
    Türkçe alan adlarıyla döndürür.
    """
    leads = get_leads()

    return [
        {
            "id": lead["id"],
            "isim": lead["name"],
            "telefon": lead["phone"],
            "mesaj": lead["message"],
            "email": lead["email"],
            "tarih": lead["created_at"],
        }
        for lead in leads
    ]


# Eski fonksiyon adlarıyla uyumluluk
lead_ekle = create_lead
