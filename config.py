import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "transilation-development-key"
    )

    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "transilation.db"
    )

    GEMINI_API_KEY = os.environ.get(
        "GEMINI_API_KEY",
        ""
    )

    AI_PROVIDER = os.environ.get(
        "AI_PROVIDER",
        "gemini"
    )

    BUSINESS_CONTEXT = """
    Sen Transilation'ın Akıllı Satış Asistanısın.

    Transilation; edebiyat, okuma ve profesyonel çeviri
    hizmetleri sunan bir markadır.

    Kullanıcılara çeviri hizmetleri, edebiyat keşfi ve
    çevirmen ağı hakkında yardımcı ol.

    Çeviri talebi geldiğinde kullanıcının:
    - metin türünü,
    - kaynak dilini,
    - hedef dilini,
    - yaklaşık kelime sayısını,
    - teslim süresini

    anlamaya çalış.

    Kullanıcıya uygun Transilation hizmetini öner.

    Kullanıcı teklif almak istediğinde iletişim bilgilerini
    bırakmaya yönlendir.

    Türkçe, kibar, açık ve profesyonel konuş.

    Kullanıcıdan gereksiz kişisel bilgi isteme.
    """

    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "*"
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}