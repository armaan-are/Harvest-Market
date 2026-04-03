"""Basic Flask API routes for milestone 5."""

from __future__ import annotations

from flask import Flask, jsonify, request

from backend.api_handlers import (
    create_message_record,
    create_product_record,
    create_purchase_record,
    delete_product_record,
    get_sorted_products,
    get_visible_messages,
    login_user,
    register_user,
    update_product_record,
)
from backend import mock_state


app = Flask(__name__)


def reset_mock_state() -> None:
    """Reset in-memory data so tests start from a clean known state."""
    mock_state.reset_mock_state()


def create_app() -> Flask:
    """Application factory used by both local runs and tests."""
    return app


@app.after_request
def add_cors_headers(response):
    """Allow the frontend to call the mock API during local development."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.get("/api/health")
def health():
    """Return a simple health response."""
    return jsonify({"status": "ok", "message": "Flask backend is running!"})


@app.post("/api/register")
def register():
    """Create a new mock user account."""
    body = request.get_json(silent=True) or {}
    payload, status = register_user(
        body.get("email"),
        body.get("password"),
        body.get("role"),
    )
    return jsonify(payload), status


@app.post("/api/login")
def login():
    """Log in and return a simple mock token."""
    body = request.get_json(silent=True) or {}
    payload, status = login_user(body.get("email"), body.get("password"))
    return jsonify(payload), status


@app.get("/api/products")
def list_products():
    """Return products, optionally sorted for the frontend."""
    sort = request.args.get("sort", "default")
    payload, status = get_sorted_products(sort)
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


@app.get("/api/messages")
def get_messages():
    """Return the messages a user can see for a product."""
    current_user, error = _get_current_user()
    if error:
        return error

    product_id = request.args.get("productId", type=int)
    payload, status = get_visible_messages(current_user, product_id)
    return jsonify(payload), status


@app.post("/api/messages")
def post_message():
    """Send a new mock message about a product."""
    current_user, error = _get_current_user()
    if error:
        return error

    body = request.get_json(silent=True) or {}
    payload, status = create_message_record(current_user, body)
    return jsonify(payload), status


@app.post("/api/purchases")
def create_purchase():
    """Create a purchase for a buyer and update popularity."""
    current_user, error = _get_current_user()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    payload, status = create_purchase_record(current_user, body)
    return jsonify(payload), status


def _get_current_user():
    """Return the logged-in user from the bearer token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, (jsonify({"detail": "Missing bearer token"}), 401)

    token = auth_header.removeprefix("Bearer ").strip()
    for user in mock_state.STATE["users"]:
        if token == mock_state.make_token(user):
            return user, None

    return None, (jsonify({"detail": "Invalid token"}), 401)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
