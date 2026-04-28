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
SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Team 21 Local Farm Marketplace API",
        "description": "SQLite-backed API for the local farm marketplace.",
        "version": "1.0.0",
    },
    "basePath": "/",
    "schemes": ["http"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Use `Bearer <token>` from the login endpoint.",
        }
    },
    "definitions": {
        "Category": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "name": {"type": "string", "example": "Produce"},
            },
        },
        "Product": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 2},
                "title": {"type": "string", "example": "Free Range Eggs"},
                "description": {"type": "string", "example": "One dozen local eggs."},
                "price": {"type": "number", "format": "float", "example": 6.5},
                "quantity_available": {"type": "integer", "example": 10},
                "quantity_reserved": {"type": "integer", "example": 0},
                "image_url": {"type": "string", "example": "/fruits/apple1.png"},
                "seller_id": {"type": "integer", "example": 2},
                "purchase_count": {"type": "integer", "example": 4},
                "farm_name": {"type": "string", "example": "Mansfield Farm"},
                "zip_code": {"type": "string", "example": "06268"},
                "category": {"type": "string", "example": "produce"},
                "average_rating": {"type": "number", "format": "float", "example": 4.75},
            },
        },
        "ProductInput": {
            "type": "object",
            "required": ["title", "price", "category"],
            "properties": {
                "title": {"type": "string", "example": "Fresh Lettuce"},
                "description": {"type": "string", "example": "Crisp and green."},
                "price": {"type": "number", "format": "float", "example": 4.25},
                "quantity_available": {"type": "integer", "example": 12},
                "category": {"type": "string", "example": "produce"},
                "image_url": {"type": "string", "example": "/fruits/orange1.png"},
            },
        },
        "Message": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "product_id": {"type": "integer", "example": 2},
                "buyer_id": {"type": "integer", "example": 1},
                "seller_id": {"type": "integer", "example": 2},
                "sender_id": {"type": "integer", "example": 1},
                "sender_role": {"type": "string", "example": "buyer"},
                "sender_email": {"type": "string", "example": "buyer@example.com"},
                "content": {"type": "string", "example": "Can I pick this up tomorrow?"},
                "created_at": {"type": "string", "example": "2026-04-28T12:00:00"},
            },
        },
        "Order": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "buyer_id": {"type": "integer", "example": 1},
                "seller_id": {"type": "integer", "example": 2},
                "status": {"type": "string", "example": "pending"},
                "pickup_window": {"type": "string", "example": "Saturday 10:00"},
                "created_at": {"type": "string", "example": "2026-04-28T12:00:00"},
            },
        },
        "Profile": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "email": {"type": "string", "example": "buyer@example.com"},
                "role": {"type": "string", "example": "buyer"},
                "full_name": {"type": "string", "example": "Finn Harrison"},
                "phone": {"type": "string", "example": "860-111-2222"},
                "home_zip": {"type": "string", "example": "06032"},
            },
        },
        "Review": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "order_id": {"type": "integer", "example": 1},
                "farmer_id": {"type": "integer", "example": 2},
                "buyer_id": {"type": "integer", "example": 1},
                "rating": {"type": "integer", "example": 5},
                "comment": {"type": "string", "example": "Great pickup and produce quality."},
                "created_at": {"type": "string", "example": "2026-04-28T12:00:00"},
            },
        },
        "Error": {
            "type": "object",
            "properties": {
                "detail": {"type": "string", "example": "Missing bearer token"},
            },
        },
    },
    "paths": {
        "/api/health": {
            "get": {
                "tags": ["System"],
                "summary": "Check backend health",
                "responses": {
                    "200": {
                        "description": "Backend is running",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string", "example": "ok"},
                                "message": {
                                    "type": "string",
                                    "example": "Flask backend is running!",
                                },
                            },
                        },
                    }
                },
            }
        },
        "/api/categories": {
            "get": {
                "tags": ["Marketplace"],
                "summary": "List product categories",
                "responses": {
                    "200": {
                        "description": "Category list",
                        "schema": {"type": "array", "items": {"$ref": "#/definitions/Category"}},
                    }
                },
            }
        },
        "/api/register": {
            "post": {
                "tags": ["Auth"],
                "summary": "Create a buyer or seller account",
                "parameters": [
                    {
                        "in": "body",
                        "name": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["email", "password", "role"],
                            "properties": {
                                "email": {"type": "string", "example": "newbuyer@example.com"},
                                "password": {"type": "string", "example": "testpass"},
                                "role": {"type": "string", "enum": ["buyer", "seller"]},
                            },
                        },
                    }
                ],
                "responses": {
                    "201": {"description": "Registration successful"},
                    "400": {"description": "Invalid registration fields", "schema": {"$ref": "#/definitions/Error"}},
                    "409": {"description": "Email already registered", "schema": {"$ref": "#/definitions/Error"}},
                },
            }
        },
        "/api/login": {
            "post": {
                "tags": ["Auth"],
                "summary": "Log in and receive a bearer token",
                "parameters": [
                    {
                        "in": "body",
                        "name": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["email", "password"],
                            "properties": {
                                "email": {"type": "string", "example": "buyer@example.com"},
                                "password": {"type": "string", "example": "buyerpass"},
                            },
                        },
                    }
                ],
                "responses": {
                    "200": {"description": "Login successful"},
                    "401": {"description": "Invalid credentials", "schema": {"$ref": "#/definitions/Error"}},
                },
            }
        },
        "/api/products": {
            "get": {
                "tags": ["Marketplace"],
                "summary": "List products with sorting and filters",
                "parameters": [
                    {"in": "query", "name": "sort", "type": "string", "enum": ["default", "price_asc", "price_desc", "popular"]},
                    {"in": "query", "name": "category", "type": "string", "example": "produce"},
                    {"in": "query", "name": "zipCode", "type": "string", "example": "06268"},
                ],
                "responses": {
                    "200": {
                        "description": "Product list",
                        "schema": {"type": "array", "items": {"$ref": "#/definitions/Product"}},
                    }
                },
            },
            "post": {
                "tags": ["Marketplace"],
                "summary": "Create a seller product listing",
                "security": [{"Bearer": []}],
                "parameters": [{"in": "body", "name": "body", "required": True, "schema": {"$ref": "#/definitions/ProductInput"}}],
                "responses": {
                    "200": {"description": "Product created"},
                    "401": {"description": "Missing or invalid token", "schema": {"$ref": "#/definitions/Error"}},
                    "403": {"description": "Seller access required", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
        },
        "/api/products/{product_id}": {
            "put": {
                "tags": ["Marketplace"],
                "summary": "Update a seller product listing",
                "security": [{"Bearer": []}],
                "parameters": [
                    {"in": "path", "name": "product_id", "type": "integer", "required": True},
                    {"in": "body", "name": "body", "required": True, "schema": {"$ref": "#/definitions/ProductInput"}},
                ],
                "responses": {
                    "200": {"description": "Product updated"},
                    "400": {"description": "Invalid product payload", "schema": {"$ref": "#/definitions/Error"}},
                    "403": {"description": "Not allowed to update product", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
            "delete": {
                "tags": ["Marketplace"],
                "summary": "Delete a seller product listing",
                "security": [{"Bearer": []}],
                "parameters": [{"in": "path", "name": "product_id", "type": "integer", "required": True}],
                "responses": {
                    "200": {"description": "Product deleted"},
                    "403": {"description": "Not allowed to delete product", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
        },
        "/api/uploads": {
            "post": {
                "tags": ["Marketplace"],
                "summary": "Upload a product image",
                "consumes": ["multipart/form-data"],
                "security": [{"Bearer": []}],
                "parameters": [
                    {"in": "formData", "name": "image", "type": "file", "required": True}
                ],
                "responses": {
                    "201": {"description": "Image uploaded"},
                    "403": {"description": "Seller access required", "schema": {"$ref": "#/definitions/Error"}},
                },
            }
        },
        "/api/messages": {
            "get": {
                "tags": ["Messages"],
                "summary": "List visible product messages",
                "security": [{"Bearer": []}],
                "parameters": [{"in": "query", "name": "productId", "type": "integer", "required": True}],
                "responses": {
                    "200": {"description": "Messages", "schema": {"type": "array", "items": {"$ref": "#/definitions/Message"}}},
                    "401": {"description": "Missing or invalid token", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
            "post": {
                "tags": ["Messages"],
                "summary": "Send a product-linked message",
                "security": [{"Bearer": []}],
                "parameters": [
                    {
                        "in": "body",
                        "name": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["productId", "content"],
                            "properties": {
                                "productId": {"type": "integer", "example": 2},
                                "content": {"type": "string", "example": "Can I pick this up tomorrow?"},
                            },
                        },
                    }
                ],
                "responses": {
                    "201": {"description": "Message sent"},
                    "400": {"description": "Invalid message payload", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
        },
        "/api/orders": {
            "get": {
                "tags": ["Orders"],
                "summary": "List current user's orders",
                "security": [{"Bearer": []}],
                "parameters": [{"in": "query", "name": "status", "type": "string", "example": "pending"}],
                "responses": {
                    "200": {"description": "Orders", "schema": {"type": "array", "items": {"$ref": "#/definitions/Order"}}},
                    "401": {"description": "Missing or invalid token", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
            "post": {
                "tags": ["Orders"],
                "summary": "Create a pending order",
                "security": [{"Bearer": []}],
                "parameters": [
                    {
                        "in": "body",
                        "name": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["productId"],
                            "properties": {
                                "productId": {"type": "integer", "example": 2},
                                "quantity": {"type": "integer", "example": 1},
                                "pickupWindow": {"type": "string", "example": "Saturday 10:00"},
                            },
                        },
                    }
                ],
                "responses": {
                    "201": {"description": "Order created"},
                    "400": {"description": "Invalid order payload", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
        },
        "/api/orders/{order_id}/status": {
            "put": {
                "tags": ["Orders"],
                "summary": "Advance, reject, or cancel an order",
                "security": [{"Bearer": []}],
                "parameters": [
                    {"in": "path", "name": "order_id", "type": "integer", "required": True},
                    {
                        "in": "body",
                        "name": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["status"],
                            "properties": {
                                "status": {
                                    "type": "string",
                                    "enum": ["confirmed", "ready_for_pickup", "completed", "rejected", "cancelled"],
                                }
                            },
                        },
                    },
                ],
                "responses": {
                    "200": {"description": "Order status updated"},
                    "400": {"description": "Invalid status transition", "schema": {"$ref": "#/definitions/Error"}},
                    "403": {"description": "Not allowed to update order", "schema": {"$ref": "#/definitions/Error"}},
                },
            }
        },
        "/api/purchases": {
            "post": {
                "tags": ["Orders"],
                "summary": "Create a pending order through the legacy purchase route",
                "security": [{"Bearer": []}],
                "parameters": [
                    {
                        "in": "body",
                        "name": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["productId"],
                            "properties": {
                                "productId": {"type": "integer", "example": 2},
                                "quantity": {"type": "integer", "example": 1},
                            },
                        },
                    }
                ],
                "responses": {"201": {"description": "Purchase/order created"}},
            }
        },
        "/api/profile": {
            "get": {
                "tags": ["Profiles"],
                "summary": "Fetch current user's profile",
                "security": [{"Bearer": []}],
                "responses": {
                    "200": {"description": "Profile", "schema": {"$ref": "#/definitions/Profile"}},
                    "401": {"description": "Missing or invalid token", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
            "put": {
                "tags": ["Profiles"],
                "summary": "Update current user's profile",
                "security": [{"Bearer": []}],
                "parameters": [{"in": "body", "name": "body", "required": True, "schema": {"$ref": "#/definitions/Profile"}}],
                "responses": {
                    "200": {"description": "Profile updated", "schema": {"$ref": "#/definitions/Profile"}},
                    "400": {"description": "Invalid profile payload", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
        },
        "/api/reviews": {
            "get": {
                "tags": ["Reviews"],
                "summary": "List community reviews",
                "parameters": [{"in": "query", "name": "farmerId", "type": "integer"}],
                "responses": {
                    "200": {"description": "Reviews", "schema": {"type": "array", "items": {"$ref": "#/definitions/Review"}}}
                },
            },
            "post": {
                "tags": ["Reviews"],
                "summary": "Create a verified review for a completed order",
                "security": [{"Bearer": []}],
                "parameters": [
                    {
                        "in": "body",
                        "name": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["orderId", "rating"],
                            "properties": {
                                "orderId": {"type": "integer", "example": 1},
                                "rating": {"type": "integer", "minimum": 1, "maximum": 5, "example": 5},
                                "comment": {"type": "string", "example": "Great pickup and produce quality."},
                            },
                        },
                    }
                ],
                "responses": {
                    "201": {"description": "Review created"},
                    "400": {"description": "Invalid review payload", "schema": {"$ref": "#/definitions/Error"}},
                },
            },
        },
    },
}
Swagger(app, template=SWAGGER_TEMPLATE)


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
