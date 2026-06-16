import os
from flask import Flask, session
from dotenv import load_dotenv
from config import Config
from app.models.db import init_db

def create_app():
    # Load environment variables (e.g. SECRET_KEY, etc.)
    load_dotenv()
    
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance and upload folders exist
    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize the database if database file doesn't exist
    if not os.path.exists(app.config['DATABASE']):
        print("Initializing database...")
        init_db()

    # Register Blueprints
    from app.routes import auth_bp, user_bp, item_bp, board_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(board_bp)

    # Inject current user context into templates globally
    @app.context_processor
    def inject_user():
        from app.models.user import User
        user_id = session.get('user_id')
        if user_id:
            try:
                user = User.get_by_id(user_id)
                return dict(current_user=user)
            except Exception:
                pass
        return dict(current_user=None)

    return app
