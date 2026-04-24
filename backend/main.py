"""Flask API routes for the local farm marketplace."""

from __future__ import annotations

from pathlib import Path

from flasgger import Swagger
from flask import Flask, jsonify, request, send_from_directory

from backend.api_handlers import (
    create_message_record,
    create_order_record,
    create_product_record,
    create_review_record,
    delete_product_record,
    get_categories,
    get_profile,
    get_sorted_products,
    get_user_from_token,
    get_visible_messages,
    list_orders_for_user,
    list_reviews,
    login_user,
    register_user,
    update_order_status_record,
    update_product_record,
    update_profile,
)
from backend.db import UPLOAD_DIR, reset_database, save_upload


app = Flask(__name__)
app.config["SWAGGER"] = {
    "title": "Team 21 Local Farm Marketplace API",
    "uiversion": 3,
}
Swagger(app)


def reset_mock_state() -> None:
    """Reset the sqlite db to a clean seeded state for tests."""
    reset_database()


def create_app() -> Flask:
    """Application factory used by both local runs and tests."""
    return app


@app.after_request
def add_cors_headers(response):
    """Allow the frontend to call the API during local development."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.get("/api/health")
def health():
    """Return a simple health response."""
    return jsonify({"status": "ok", "message": "Flask backend is running!"})


@app.get("/api/categories")
def categories():
    """Return product categories."""
    payload, status = get_categories()
    return jsonify(payload), status


@app.post("/api/register")
def register():
    """Create a new user account."""
    body = request.get_json(silent=True) or {}
    payload, status = register_user(
        body.get("email"),
        body.get("password"),
        body.get("role"),
    )
    return jsonify(payload), status


@app.post("/api/login")
def login():
    """Log in and return a simple bearer token."""
    body = request.get_json(silent=True) or {}
    payload, status = login_user(body.get("email"), body.get("password"))
    return jsonify(payload), status


@app.get("/api/products")
def list_products():
    """Return products with sort and filter support."""
    payload, status = get_sorted_products(
        request.args.get("sort", "default"),
        request.args.get("category"),
        request.args.get("zipCode"),
    )
    return jsonify(payload), status


@app.post("/api/products")
def create_product():
    """Create a product for a seller."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = create_product_record(current_user, body)
    return jsonify(payload), status


@app.put("/api/products/<int:product_id>")
def update_product(product_id: int):
    """Update a seller's own product."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = update_product_record(current_user, product_id, body)
    return jsonify(payload), status


@app.delete("/api/products/<int:product_id>")
def delete_product(product_id: int):
    """Delete a seller's own product."""
    current_user, error = _get_current_user()
    if error:
        return error
    payload, status = delete_product_record(current_user, product_id)
    return jsonify(payload), status


@app.post("/api/uploads")
def upload_image():
    """Store a product image file and return the public path."""
    current_user, error = _get_current_user()
    if error:
        return error
    if current_user["role"] != "seller":
        return jsonify({"detail": "Only sellers can upload listing images"}), 403

    file_storage = request.files.get("image")
    if file_storage is None or not file_storage.filename:
        return jsonify({"detail": "image is required"}), 400

    return jsonify({"imagePath": save_upload(file_storage)}), 201


@app.get("/uploads/<path:filename>")
def uploaded_file(filename: str):
    """Serve uploaded images."""
    return send_from_directory(Path(UPLOAD_DIR), filename)


@app.get("/api/messages")
def get_messages():
    """Return the messages a user can see for a product."""
    current_user, error = _get_current_user()
    if error:
        return error
    payload, status = get_visible_messages(current_user, request.args.get("productId", type=int))
    return jsonify(payload), status


@app.post("/api/messages")
def post_message():
    """Send a new product-linked message."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = create_message_record(current_user, body)
    return jsonify(payload), status


@app.post("/api/orders")
def create_order():
    """Create a pending order."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = create_order_record(current_user, body)
    return jsonify(payload), status


@app.get("/api/orders")
def list_orders():
    """List orders for the current user."""
    current_user, error = _get_current_user()
    if error:
        return error
    payload, status = list_orders_for_user(current_user, request.args.get("status"))
    return jsonify(payload), status


@app.put("/api/orders/<int:order_id>/status")
def update_order_status(order_id: int):
    """Advance or close an order."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = update_order_status_record(current_user, order_id, body.get("status"))
    return jsonify(payload), status


@app.post("/api/purchases")
def create_purchase():
    """Backward-compatible route for the old purchase action."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = create_order_record(current_user, body)
    return jsonify(payload), status


@app.get("/api/profile")
def current_profile():
    """Return the current user's profile."""
    current_user, error = _get_current_user()
    if error:
        return error
    payload, status = get_profile(current_user)
    return jsonify(payload), status


@app.put("/api/profile")
def save_profile():
    """Update the current user's profile."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = update_profile(current_user, body)
    return jsonify(payload), status


@app.get("/api/reviews")
def reviews():
    """Return reviews for community and trust screens."""
    payload, status = list_reviews(request.args.get("farmerId", type=int))
    return jsonify(payload), status


@app.post("/api/reviews")
def create_review():
    """Create a verified review for a completed order."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = create_review_record(current_user, body)
    return jsonify(payload), status


def _get_current_user():
    """Return the logged-in user from the bearer token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, (jsonify({"detail": "Missing bearer token"}), 401)

    token = auth_header.removeprefix("Bearer ").strip()
    user = get_user_from_token(token)
    if user is None:
        return None, (jsonify({"detail": "Invalid token"}), 401)
    return user, None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
