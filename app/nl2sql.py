import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from config import active_config

logger = logging.getLogger(__name__)


def get_enriched_schema() -> str:
    """
    Returns a hand-crafted, semantically enriched schema description.
    This is the knowledge base the LLM uses to understand the data.
    """
    return """
========== DATABASE: orders_db ==========

TABLE: orders_db.orders  (one row per order)
  - order_id                        : unique order identifier — links to order_items, order_payments, order_reviews
  - customer_id                     : links to orders_db.customers.customer_id
  - order_status                    : current state of order — values: delivered, shipped, canceled, invoiced, processing, approved, unavailable
  - order_purchase_timestamp        : SEMANTIC → "order date", "when ordered", "purchase date", "order placed date"
  - order_approved_at               : SEMANTIC → "approval date", "when approved"
  - order_delivered_carrier_date    : SEMANTIC → "shipped date", "handed to carrier", "dispatch date"
  - order_delivered_customer_date   : SEMANTIC → "delivery date", "date delivered", "when delivered", "actual delivery", "date it was delivered", "received date"
  - order_estimated_delivery_date   : SEMANTIC → "estimated delivery", "expected delivery date", "promised delivery", "due date"
  NOTE: Late delivery = order_delivered_customer_date > order_estimated_delivery_date

TABLE: orders_db.customers  (one row per unique customer address)
  - customer_id                     : links to orders_db.orders.customer_id
  - customer_unique_id              : true unique customer identifier (one customer can have multiple customer_ids)
  - customer_zip_code_prefix        : first 5 digits of ZIP code
  - customer_city                   : SEMANTIC → "city", "customer city", "buyer city"
  - customer_state                  : SEMANTIC → "state", "customer state", "region" — 2-letter Brazil state code

TABLE: orders_db.order_items  (one row per product in an order — one order can have multiple rows)
  - order_id                        : links to orders_db.orders.order_id
  - order_item_id                   : sequence number of item within the order (1, 2, 3...)
  - product_id                      : links to sellers_db.products.product_id
  - seller_id                       : links to sellers_db.sellers.seller_id
  - shipping_limit_date             : deadline for seller to ship
  - price                           : SEMANTIC → "item price", "product price", "cost", "sale price"
  - freight_value                   : SEMANTIC → "shipping cost", "delivery cost", "freight", "shipping fee"

TABLE: orders_db.order_payments  (one row per payment — one order can have multiple payment methods)
  - order_id                        : links to orders_db.orders.order_id
  - payment_sequential              : sequence number when multiple payments used
  - payment_type                    : SEMANTIC → "payment method", "how paid" — values: credit_card, boleto, voucher, debit_card
  - payment_installments            : SEMANTIC → "installments", "number of installments", "EMI count"
  - payment_value                   : SEMANTIC → "amount paid", "payment amount", "revenue", "total payment", "transaction value"

TABLE: orders_db.order_reviews  (one row per review)
  - review_id                       : unique review identifier
  - order_id                        : links to orders_db.orders.order_id
  - review_score                    : SEMANTIC → "rating", "stars", "review", "score", "customer satisfaction" — integer 1 to 5
  - review_comment_title            : short title of review
  - review_comment_message          : full review text
  - review_creation_date            : when customer submitted review
  - review_answer_timestamp         : when seller responded to review

========== DATABASE: sellers_db ==========

TABLE: sellers_db.products  (one row per product)
  - product_id                      : links to orders_db.order_items.product_id
  - product_category_name           : category in PORTUGUESE — links to sellers_db.product_category_name_translation.category_name_portuguese
  - product_name_length             : number of characters in product name
  - product_description_length      : number of characters in product description
  - product_photos_qty              : SEMANTIC → "number of photos", "photo count"
  - product_weight_g                : SEMANTIC → "weight", "product weight" — in grams
  - product_length_cm               : product length in centimeters
  - product_height_cm               : product height in centimeters
  - product_width_cm                : product width in centimeters

TABLE: sellers_db.sellers  (one row per seller)
  - seller_id                       : links to orders_db.order_items.seller_id
  - seller_zip_code_prefix          : seller ZIP code prefix
  - seller_city                     : SEMANTIC → "seller city", "seller location", "where seller is based"
  - seller_state                    : SEMANTIC → "seller state", "seller region" — 2-letter Brazil state code

TABLE: sellers_db.product_category_name_translation  (maps Portuguese category names to English)
  - category_name_portuguese        : links to sellers_db.products.product_category_name
  - category_name_english           : SEMANTIC → "category", "product category", "category name", "type of product"

TABLE: sellers_db.geolocation  (ZIP code to coordinates mapping)
  - geolocation_zip_code_prefix     : links to customers.customer_zip_code_prefix or sellers.seller_zip_code_prefix
  - geolocation_lat                 : latitude
  - geolocation_lng                 : longitude
  - geolocation_city                : city name
  - geolocation_state               : state code

========== KEY RELATIONSHIPS ==========

orders_db.orders.order_id              → orders_db.order_items.order_id
orders_db.orders.order_id              → orders_db.order_payments.order_id
orders_db.orders.order_id              → orders_db.order_reviews.order_id
orders_db.orders.customer_id           → orders_db.customers.customer_id
orders_db.order_items.product_id       → sellers_db.products.product_id
orders_db.order_items.seller_id        → sellers_db.sellers.seller_id
sellers_db.products.product_category_name → sellers_db.product_category_name_translation.category_name_portuguese
"""


def build_prompt_template() -> PromptTemplate:
    template = """
You are an expert MySQL analyst for a Brazilian e-commerce company (Olist).
You query two databases: orders_db and sellers_db.

{schema}

========== SQL RULES ==========
1. ONLY write SELECT statements. Never write INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE.
2. ALWAYS prefix every table with its database: orders_db.table_name or sellers_db.table_name
3. Return ONLY the raw SQL query. No explanation. No markdown. No triple backticks.
4. If the question cannot be answered from the schema, return exactly: CANNOT_GENERATE
5. For date filtering use: YEAR(column) = 2018 or DATE(column) = '2018-01-01'
6. For late deliveries use: order_delivered_customer_date > order_estimated_delivery_date
7. Always use meaningful aliases (AS total_orders, AS revenue, AS avg_score)
8. For category names always JOIN with product_category_name_translation to show English names

========== EXAMPLES ==========

Question: How many orders were delivered late?
SQL: SELECT COUNT(*) AS late_deliveries FROM orders_db.orders WHERE order_delivered_customer_date > order_estimated_delivery_date;

Question: What was the date it was delivered for order 'abc123'?
SQL: SELECT order_id, order_delivered_customer_date AS delivery_date FROM orders_db.orders WHERE order_id = 'abc123';

Question: Which product category had the most orders?
SQL: SELECT t.category_name_english, COUNT(oi.order_id) AS total_orders FROM orders_db.order_items oi JOIN sellers_db.products p ON oi.product_id = p.product_id JOIN sellers_db.product_category_name_translation t ON p.product_category_name = t.category_name_portuguese GROUP BY t.category_name_english ORDER BY total_orders DESC LIMIT 10;

Question: Top 5 sellers by revenue?
SQL: SELECT oi.seller_id, ROUND(SUM(oi.price), 2) AS total_revenue FROM orders_db.order_items oi GROUP BY oi.seller_id ORDER BY total_revenue DESC LIMIT 5;

Question: Average review score by state?
SQL: SELECT c.customer_state, ROUND(AVG(r.review_score), 2) AS avg_score FROM orders_db.order_reviews r JOIN orders_db.orders o ON r.order_id = o.order_id JOIN orders_db.customers c ON o.customer_id = c.customer_id GROUP BY c.customer_state ORDER BY avg_score DESC;

========== NOW ANSWER THIS ==========
Question: {question}
SQL:
"""
    return PromptTemplate(
        input_variables=["schema", "question"],
        template=template
    )


def generate_sql(natural_language_query: str) -> dict:
    logger.info(f"Generating SQL for: '{natural_language_query}'")
    try:
        schema_text = get_enriched_schema()

        prompt_template = build_prompt_template()
        prompt = prompt_template.format(
            schema=schema_text,
            question=natural_language_query
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=active_config.GEMINI_KEY
        )

        response = llm.invoke(prompt)
        generated_sql = response.content.strip()
        logger.info(f"SQL generated: {generated_sql[:100]}...")

        if generated_sql == "CANNOT_GENERATE":
            logger.warning(f"LLM could not generate SQL for: '{natural_language_query}'")
            return {
                "status": "error",
                "message": "Could not generate SQL for this question",
                "original_query": natural_language_query,
                "sql": None
            }

        return {
            "status": "success",
            "original_query": natural_language_query,
            "sql": generated_sql
        }

    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "original_query": natural_language_query,
            "sql": None
        }