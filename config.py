import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

class Config:
    """Uygulama genel ayarlarını yöneten sınıf."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-12345')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'smartlead.db')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'groq')
    
    BUSINESS_CONTEXT = os.environ.get(
        'BUSINESS_CONTEXT', 
        'Sen Cafe Mola nin dijital asistanisin. Menu, fiyatlar ve rezervasyon hakkinda samimi sekilde Türkçe yanit ver.'
    )
    
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}