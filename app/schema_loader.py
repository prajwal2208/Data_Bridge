import logging
from sqlalchemy import inspect
from app.db import orders_engine, sellers_engine

logger = logging.getLogger(__name__)


def get_schema(engine, db_name):
    if engine is None:
        logger.warning(f"Engine for {db_name} is None — skipping")
        return {}
    try:
        inspector = inspect(engine)
        schema = {}
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            schema[table_name] = [col["name"] for col in columns]
            logger.debug(f"{db_name}.{table_name} → "
                         f"{len(columns)} columns")
        logger.info(f"Schema loaded for {db_name}: "
                    f"{len(schema)} tables found")
        return schema
    except Exception as e:
        logger.error(f"Failed to load schema for {db_name}: {e}")
        return {}


def get_all_schemas():
    logger.info("Loading schemas for all databases")
    return {
        "orders_db": get_schema(orders_engine, "orders_db"),
        "sellers_db": get_schema(sellers_engine, "sellers_db")
    }