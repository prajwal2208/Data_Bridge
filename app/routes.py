import logging
from flask import Blueprint, jsonify,request
from app.schema_loader import get_all_schemas
from app.nl2sql import generate_sql

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.route("/health", methods=["GET"])
def health():
    logger.info("Health check called")
    return jsonify({
        "status": "ok",
        "message": "DataBridge is running"
    }), 200


@main_bp.route("/schema", methods=["GET"])
def schema():
    logger.info("Schema endpoint called")
    try:
        all_schemas = get_all_schemas()
        return jsonify(all_schemas), 200
    except Exception as e:
        logger.error(f"Schema endpoint error: {e}")
        return jsonify({"error": str(e)}), 500
    

@main_bp.route("/generate-sql", methods=["POST"])      # ← added
def generate_sql_endpoint():
    logger.info("Generate SQL endpoint called")

    data = request.get_json()
    if not data or "query" not in data:
        logger.warning("Request missing 'query' field")
        return jsonify({
            "error": "Request body must contain 'query' field"
        }), 400

    natural_language_query = data["query"].strip()
    if not natural_language_query:
        logger.warning("Empty query received")
        return jsonify({"error": "Query cannot be empty"}), 400

    result = generate_sql(natural_language_query)

    if result["status"] == "error":
        return jsonify(result), 500

    return jsonify(result), 200    