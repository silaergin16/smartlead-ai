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
        "smartlead.db"
    )

    GROQ_API_KEY = os.environ.get(
        "GROQ_API_KEY",
        ""
    )

    GEMINI_API_KEY = os.environ.get(
        "GEMINI_API_KEY",
        ""
    )

    AI_PROVIDER = os.environ.get(
        "AI_PROVIDER",
        "groq"
    )

    BUSINESS_CONTEXT = os.environ.get(
        "BUSINESS_CONTEXT",
        "Sen Transilation'ın kibar ve yardımsever Türkçe satış asistanısın."
    )

    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "*"
    ).split(",")

    # Dashboard güvenliği
    ADMIN_USERNAME = os.environ.get(
        "ADMIN_USERNAME",
        "admin"
    )

    ADMIN_PASSWORD = os.environ.get(
        "ADMIN_PASSWORD",
        "change-this-password"
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


config = config_by_name