import logging
from sqlalchemy import create_engine
from config import active_config

logger = logging.getLogger(__name__)

try:
    orders_engine = create_engine(active_config.ORDERS_DB_URL)
    logger.info("orders_db engine created successfully")
except Exception as e:
    logger.error(f"Failed to create orders_db engine: {e}")
    orders_engine = None

try:
    sellers_engine = create_engine(active_config.SELLERS_DB_URL)
    logger.info("sellers_db engine created successfully")
except Exception as e:
    logger.error(f"Failed to create sellers_db engine: {e}")
    sellers_engine = None