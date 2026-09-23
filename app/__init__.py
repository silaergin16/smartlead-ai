from flask import Flask

from config import DevelopmentConfig
from app.database import init_db


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates"
    )

    app.config.from_object(DevelopmentConfig)

    from app.routes import main
    app.register_blueprint(main)

    init_db()

    return app