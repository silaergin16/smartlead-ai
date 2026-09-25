from flask import Flask, jsonify
from flask_cors import CORS
from config import config_by_name
from app.database import init_db, close_db

def create_app(config_name='development'):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_by_name[config_name])
    
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    
    init_db(app)
    app.teardown_appcontext(close_db)
    
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/health')
    def health():
        return jsonify({"durum": "canli", "sistem": "SmartLead AI Backend"}), 200

    return app