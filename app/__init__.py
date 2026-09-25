from flask import Flask
from flask_cors import CORS

from config import DevelopmentConfig
from app.database import init_db


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates"
    )

    app.config.from_object(DevelopmentConfig)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type"]
            }
        }
    )

    from app.routes import main
    app.register_blueprint(main)

    init_db()

    return app