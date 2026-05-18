import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key")
    DEBUG = False
    TESTING = False
    ORDERS_DB_URL = os.getenv("ORDERS_DB_URL")
    SELLERS_DB_URL = os.getenv("SELLERS_DB_URL")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_FILE = "logs/app.log"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}

active_config = config_map.get(
    os.getenv("FLASK_ENV", "development"),
    DevelopmentConfig
)