import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Load environment variables
    load_dotenv()

    # Initialize Flask app
    app = Flask(__name__, instance_relative_config=True)

    # Set default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev_secret_key_heart_check_98765'),
        DATABASE=os.path.join(app.instance_path, 'database.db'),
    )

    # Ensure the instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize the database
    from app.models.db import init_db
    try:
        init_db()
    except Exception as e:
        app.logger.error(f"Failed to initialize database on startup: {e}")

    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.item import item_bp
    from app.routes.board import board_bp

    # Registered with no url_prefix because their routes already define full paths
    # (e.g. /register, /login, /profile, /items, /announcements, etc.)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(board_bp)

    return app
