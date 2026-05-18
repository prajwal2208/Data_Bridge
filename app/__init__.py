import logging
import os
from flask import Flask
from app.routes import main_bp
from config import active_config


def create_app():
    app = Flask(__name__)

    # Load config
    app.config.from_object(active_config)

    # Setup logging
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, active_config.LOG_LEVEL, logging.DEBUG),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(active_config.LOG_FILE),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"DataBridge starting in "
                f"{os.getenv('FLASK_ENV', 'development')} mode")

    # Register blueprints
    app.register_blueprint(main_bp)

    return app