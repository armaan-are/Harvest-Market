"""Flask API routes for the Team 21 farm marketplace backend."""

from __future__ import annotations

import os

from flasgger import Swagger
from flask import Flask, jsonify, request

from backend.api_handlers import (
    create_message_record,
    create_product_record,
    create_purchase_record,
    delete_product_record,
    get_sorted_products,
    get_user_from_token,
    get_visible_messages,
    login_user,
    register_user,
    update_product_record,
)
from backend.database import DEFAULT_DB_PATH, initialize_database, reset_database


def reset_mock_state(database_path: str | None = None) -> None:
    """Reset the SQLite database so tests start from a known state."""
    path = database_path or os.environ.get("TEAM21_DB_PATH", str(DEFAULT_DB_PATH))
    reset_database(path)


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory used by local runs and tests."""
    flask_app = Flask(__name__)
    flask_app.config["SWAGGER"] = {
        "title": "Team 21 Local Farm Marketplace API",
        "uiversion": 3,
    }
    flask_app.config["DATABASE"] = os.environ.get(
        "TEAM21_DB_PATH",
        str(DEFAULT_DB_PATH),
    )
    if test_config:
        flask_app.config.update(test_config)

    initialize_database(flask_app.config["DATABASE"])
    Swagger(flask_app)

    @flask_app.after_request
    def add_cors_headers(response):
        """Allow the frontend to call the API during local development."""
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization"
        )
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        return response

    @flask_app.get("/api/health")
    def health():
        """Health check endpoint.
        ---
        tags:
          - Utility
        responses:
          200:
            description: Backend is running
            schema:
              type: object
              properties:
                status:
                  type: string
                message:
                  type: string
        """
        return jsonify({"status": "ok", "message": "Flask backend is running!"})

    @flask_app.post("/api/register")
    def register():
        """Register a new buyer or seller account.
        ---
        tags:
          - Auth
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - email
                - password
                - role
              properties:
                email:
                  type: string
                password:
                  type: string
                role:
                  type: string
                  enum: [buyer, seller]
        responses:
          201:
            description: Registration succeeded
          400:
            description: Missing or invalid fields
          409:
            description: Email already exists
        """
        body = request.get_json(silent=True) or {}
        payload, status = register_user(
            flask_app.config["DATABASE"],
            body.get("email"),
            body.get("password"),
            body.get("role"),
        )
        return jsonify(payload), status

    @flask_app.post("/api/login")
    def login():
        """Log in an existing user.
        ---
        tags:
          - Auth
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - email
                - password
              properties:
                email:
                  type: string
                password:
                  type: string
        responses:
          200:
            description: Login succeeded
          401:
            description: Invalid credentials
        """
        body = request.get_json(silent=True) or {}
        payload, status = login_user(
            flask_app.config["DATABASE"],
            body.get("email"),
            body.get("password"),
        )
        return jsonify(payload), status

    @flask_app.get("/api/products")
    def list_products():
        """List products with optional sorting.
        ---
        tags:
          - Products
        parameters:
          - in: query
            name: sort
            required: false
            type: string
            enum: [default, price_asc, price_desc, popular]
        responses:
          200:
            description: Product list
        """
        sort = request.args.get("sort", "default")
        payload, status = get_sorted_products(flask_app.config["DATABASE"], sort)
        return jsonify(payload), status

    @flask_app.post("/api/products")
    def create_product():
        """Create a product listing for the logged-in seller.
        ---
        tags:
          - Products
        security:
          - Bearer: []
        parameters:
          - in: header
            name: Authorization
            required: true
            type: string
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - title
                - price
              properties:
                title:
                  type: string
                description:
                  type: string
                price:
                  type: number
                quantity:
                  type: integer
                image_url:
                  type: string
        responses:
          201:
            description: Product created
          403:
            description: Only sellers may create products
        """
        current_user, error = _get_current_user(flask_app)
        if error:
            return error
        body = request.get_json(silent=True) or {}
        payload, status = create_product_record(
            current_user,
            body,
            flask_app.config["DATABASE"],
        )
        return jsonify(payload), status

    @flask_app.put("/api/products/<int:product_id>")
    def update_product(product_id: int):
        """Update an existing product owned by the seller.
        ---
        tags:
          - Products
        security:
          - Bearer: []
        parameters:
          - in: header
            name: Authorization
            required: true
            type: string
          - in: path
            name: product_id
            required: true
            type: integer
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                title:
                  type: string
                description:
                  type: string
                price:
                  type: number
                quantity:
                  type: integer
                image_url:
                  type: string
        responses:
          200:
            description: Product updated
          400:
            description: Invalid update fields
          403:
            description: Seller does not own the product
        """
        current_user, error = _get_current_user(flask_app)
        if error:
            return error
        body = request.get_json(silent=True) or {}
        payload, status = update_product_record(
            current_user,
            product_id,
            body,
            flask_app.config["DATABASE"],
        )
        return jsonify(payload), status

    @flask_app.delete("/api/products/<int:product_id>")
    def delete_product(product_id: int):
        """Delete a product owned by the seller.
        ---
        tags:
          - Products
        security:
          - Bearer: []
        parameters:
          - in: header
            name: Authorization
            required: true
            type: string
          - in: path
            name: product_id
            required: true
            type: integer
        responses:
          200:
            description: Product deleted
          403:
            description: Seller does not own the product
        """
        current_user, error = _get_current_user(flask_app)
        if error:
            return error
        payload, status = delete_product_record(
            current_user,
            product_id,
            flask_app.config["DATABASE"],
        )
        return jsonify(payload), status

    @flask_app.get("/api/messages")
    def get_messages():
        """Fetch product conversation messages for a participant.
        ---
        tags:
          - Messages
        security:
          - Bearer: []
        parameters:
          - in: header
            name: Authorization
            required: true
            type: string
          - in: query
            name: productId
            required: true
            type: integer
        responses:
          200:
            description: Message list
          400:
            description: Missing productId
        """
        current_user, error = _get_current_user(flask_app)
        if error:
            return error

        product_id = request.args.get("productId", type=int)
        payload, status = get_visible_messages(
            current_user,
            product_id,
            flask_app.config["DATABASE"],
        )
        return jsonify(payload), status

    @flask_app.post("/api/messages")
    def post_message():
        """Send a product-related message.
        ---
        tags:
          - Messages
        security:
          - Bearer: []
        parameters:
          - in: header
            name: Authorization
            required: true
            type: string
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - productId
                - content
              properties:
                productId:
                  type: integer
                content:
                  type: string
        responses:
          201:
            description: Message created
          403:
            description: User is not allowed in this conversation
          404:
            description: Product not found
        """
        current_user, error = _get_current_user(flask_app)
        if error:
            return error

        body = request.get_json(silent=True) or {}
        payload, status = create_message_record(
            current_user,
            body,
            flask_app.config["DATABASE"],
        )
        return jsonify(payload), status

    @flask_app.post("/api/purchases")
    def create_purchase():
        """Create a pending order and reserve product inventory.
        ---
        tags:
          - Orders
        security:
          - Bearer: []
        parameters:
          - in: header
            name: Authorization
            required: true
            type: string
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - productId
              properties:
                productId:
                  type: integer
                quantity:
                  type: integer
        responses:
          201:
            description: Pending order created
          403:
            description: Only buyers may place purchases
          409:
            description: Not enough inventory available
        """
        current_user, error = _get_current_user(flask_app)
        if error:
            return error
        body = request.get_json(silent=True) or {}
        payload, status = create_purchase_record(
            current_user,
            body,
            flask_app.config["DATABASE"],
        )
        return jsonify(payload), status

    return flask_app


def _get_current_user(flask_app: Flask):
    """Return the logged-in user from the bearer token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, (jsonify({"detail": "Missing bearer token"}), 401)

    token = auth_header.removeprefix("Bearer ").strip()
    current_user = get_user_from_token(flask_app.config["DATABASE"], token)
    if current_user is None:
        return None, (jsonify({"detail": "Invalid token"}), 401)

    return current_user, None


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
