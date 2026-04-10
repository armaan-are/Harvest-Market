"""Database-backed backend operations used by the Flask routes."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.database import (
    get_connection,
    insert_buyer_profile,
    insert_farm_profile,
    row_to_dict,
)
from backend.mock_state import make_token


ORDERED_STATUSES = ("pending", "confirmed", "ready_for_pickup", "completed")


def register_user(database_path: str, email: str, password: str, role: str):
    """Create a new user account in SQLite."""
    if not email or not password or role not in {"buyer", "seller"}:
        return {"detail": "Missing or invalid registration fields"}, 400

    created_at = _now_iso()
    with get_connection(database_path) as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if existing is not None:
            return {"detail": "Email already registered"}, 409

        cursor = connection.execute(
            """
            INSERT INTO users (email, password, role, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (email, password, role, created_at),
        )
        user_id = cursor.lastrowid

        if role == "buyer":
            insert_buyer_profile(connection, user_id, "", "", "")
        else:
            insert_farm_profile(
                connection,
                user_id,
                {
                    "farm_name": "",
                    "biography": "",
                    "pickup_address": "",
                    "operating_hours": "",
                    "zip_code": "",
                },
            )

        connection.commit()

    return {"message": "Registration successful", "userId": user_id}, 201


def login_user(database_path: str, email: str | None, password: str | None):
    """Log in and return a simple token."""
    with get_connection(database_path) as connection:
        user = connection.execute(
            """
            SELECT id, email, password, role
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    if user is None or user["password"] != password:
        return {"detail": "Invalid email or password"}, 401

    user_dict = row_to_dict(user)
    return {
        "message": "Login successful",
        "token": make_token(user_dict),
        "role": user["role"],
        "email": user["email"],
        "userId": user["id"],
    }, 200


def get_sorted_products(database_path: str, sort: str):
    """Return products and derived popularity values from SQLite."""
    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                products.id,
                products.title,
                products.description,
                products.price,
                products.image_path AS image_url,
                products.seller_id,
                products.quantity_available,
                products.quantity_reserved,
                COALESCE(SUM(
                    CASE
                        WHEN orders.status IN (
                            'pending', 'confirmed', 'ready_for_pickup', 'completed'
                        )
                        THEN order_items.quantity
                        ELSE 0
                    END
                ), 0) AS purchase_count
            FROM products
            LEFT JOIN order_items ON order_items.product_id = products.id
            LEFT JOIN orders ON orders.id = order_items.order_id
            GROUP BY products.id
            """
        ).fetchall()

    products = [dict(row) for row in rows]
    for product in products:
        product["purchase_count"] = int(product["purchase_count"])

    if sort == "price_asc":
        products.sort(key=lambda item: (item["price"], item["id"]))
    elif sort == "price_desc":
        products.sort(key=lambda item: (item["price"], item["id"]), reverse=True)
    elif sort == "popular":
        products.sort(
            key=lambda item: (item["purchase_count"], item["id"]),
            reverse=True,
        )
    else:
        products.sort(key=lambda item: item["id"], reverse=True)

    return products, 200


def create_product_record(current_user: dict, body: dict, database_path: str):
    """Create a product owned by the logged-in seller."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can create products"}, 403

    title = (body.get("title") or "").strip()
    description = (body.get("description") or "").strip()
    image_path = (body.get("image_url") or "").strip()
    quantity = body.get("quantity", 10)
    price_value, price_error = _parse_price(body.get("price"))
    quantity_value, quantity_error = _parse_quantity(quantity)

    if not title or price_error:
        return {"detail": "Title and price are required"}, 400
    if quantity_error:
        return {"detail": "Quantity must be a positive whole number"}, 400

    timestamp = _now_iso()
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO products (
                seller_id, title, description, price, quantity_available,
                quantity_reserved, image_path, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                current_user["id"],
                title,
                description,
                price_value,
                quantity_value,
                image_path,
                timestamp,
                timestamp,
            ),
        )
        connection.commit()

    return {"message": "Product created", "productId": cursor.lastrowid}, 201


def update_product_record(current_user: dict, product_id: int, body: dict, database_path: str):
    """Update a seller's own product."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can update products"}, 403

    with get_connection(database_path) as connection:
        product = connection.execute(
            """
            SELECT *
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()

        if product is None or product["seller_id"] != current_user["id"]:
            return {"detail": "You can only update your own products"}, 403

        updated_title = body.get("title", product["title"])
        updated_description = body.get("description", product["description"])
        updated_image = body.get("image_url", product["image_path"])

        price_source = body["price"] if "price" in body else product["price"]
        quantity_source = (
            body["quantity"] if "quantity" in body else product["quantity_available"]
        )
        price_value, price_error = _parse_price(price_source)
        quantity_value, quantity_error = _parse_quantity(quantity_source)
        if price_error:
            return {"detail": "Price must be a non-negative number"}, 400
        if quantity_error:
            return {"detail": "Quantity must be a positive whole number"}, 400

        if quantity_value < product["quantity_reserved"]:
            return {
                "detail": "Quantity cannot be lower than the reserved inventory"
            }, 400

        connection.execute(
            """
            UPDATE products
            SET title = ?, description = ?, price = ?, quantity_available = ?,
                image_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                updated_title,
                updated_description,
                price_value,
                quantity_value,
                updated_image,
                _now_iso(),
                product_id,
            ),
        )
        connection.commit()

    return {"message": "Product updated"}, 200


def delete_product_record(current_user: dict, product_id: int, database_path: str):
    """Delete a seller's own product."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can delete products"}, 403

    with get_connection(database_path) as connection:
        product = connection.execute(
            "SELECT seller_id FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if product is None or product["seller_id"] != current_user["id"]:
            return {"detail": "You can only delete your own products"}, 403

        connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
        connection.commit()

    return {"message": "Product deleted"}, 200


def get_visible_messages(current_user: dict, product_id: int | None, database_path: str):
    """Return messages visible to the logged-in participant."""
    if product_id is None:
        return {"detail": "productId is required"}, 400

    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                messages.id,
                messages.product_id,
                messages.buyer_id,
                messages.seller_id,
                messages.sender_id,
                users.role AS sender_role,
                users.email AS sender_email,
                messages.content,
                messages.created_at
            FROM messages
            JOIN users ON users.id = messages.sender_id
            WHERE messages.product_id = ?
              AND ? IN (messages.buyer_id, messages.seller_id)
            ORDER BY messages.id ASC
            """,
            (product_id, current_user["id"]),
        ).fetchall()

    return [dict(row) for row in rows], 200


def create_message_record(current_user: dict, body: dict, database_path: str):
    """Insert a new message for a product conversation."""
    product_id = body.get("productId")
    content = (body.get("content") or "").strip()
    if not product_id or not content:
        return {"detail": "productId and content are required"}, 400

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return {"detail": "productId and content are required"}, 400

    with get_connection(database_path) as connection:
        product = connection.execute(
            "SELECT id, seller_id FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if product is None:
            return {"detail": "Product not found"}, 404

        first_message = connection.execute(
            """
            SELECT buyer_id, seller_id
            FROM messages
            WHERE product_id = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()

        if first_message is None:
            if current_user["role"] != "buyer":
                return {"detail": "The first message must be sent by a buyer"}, 403
            buyer_id = current_user["id"]
            seller_id = product["seller_id"]
        else:
            buyer_id = first_message["buyer_id"]
            seller_id = first_message["seller_id"]
            if current_user["id"] not in {buyer_id, seller_id}:
                return {"detail": "You are not part of this conversation"}, 403

        order = connection.execute(
            """
            SELECT orders.id
            FROM orders
            JOIN order_items ON order_items.order_id = orders.id
            WHERE orders.buyer_id = ?
              AND orders.seller_id = ?
              AND order_items.product_id = ?
            ORDER BY orders.id DESC
            LIMIT 1
            """,
            (buyer_id, seller_id, product_id),
        ).fetchone()

        cursor = connection.execute(
            """
            INSERT INTO messages (
                product_id, order_id, buyer_id, seller_id, sender_id, content, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                order["id"] if order else None,
                buyer_id,
                seller_id,
                current_user["id"],
                content,
                _now_iso(),
            ),
        )
        connection.commit()

    return {"message": "Message sent", "messageId": cursor.lastrowid}, 201


def create_purchase_record(current_user: dict, body: dict, database_path: str):
    """Create a pending order and reserve inventory."""
    if current_user["role"] != "buyer":
        return {"detail": "Only buyers can purchase products"}, 403

    product_id, quantity_value, error = _validate_purchase_request(body)
    if error is not None:
        return error

    timestamp = _now_iso()
    with get_connection(database_path) as connection:
        product = connection.execute(
            """
            SELECT id, seller_id, price, quantity_available, quantity_reserved
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()
        if product is None:
            return {"detail": "Product not found"}, 404

        remaining = product["quantity_available"] - product["quantity_reserved"]
        if remaining < quantity_value:
            return {"detail": "Not enough inventory available"}, 409

        order_cursor = connection.execute(
            """
            INSERT INTO orders (
                buyer_id, seller_id, status, pickup_window, created_at, updated_at
            )
            VALUES (?, ?, 'pending', '', ?, ?)
            """,
            (current_user["id"], product["seller_id"], timestamp, timestamp),
        )
        order_id = order_cursor.lastrowid

        connection.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, product_id, quantity_value, product["price"]),
        )
        connection.execute(
            """
            UPDATE products
            SET quantity_reserved = quantity_reserved + ?, updated_at = ?
            WHERE id = ?
            """,
            (quantity_value, timestamp, product_id),
        )
        connection.commit()

    return {"message": "Purchase successful", "orderId": order_id}, 201


def get_user_from_token(database_path: str, token: str):
    """Resolve a bearer token to a user."""
    if not token.startswith("mock-token-"):
        return None

    token_parts = token.split("-")
    if len(token_parts) < 4:
        return None

    try:
        user_id = int(token_parts[2])
    except ValueError:
        return None

    with get_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT id, email, role
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    user = row_to_dict(row)
    if make_token(user) != token:
        return None
    return user


def _parse_price(value) -> tuple[float | None, bool]:
    """Validate and normalize a price field."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, True

    if parsed < 0:
        return None, True
    return parsed, False


def _parse_quantity(value) -> tuple[int | None, bool]:
    """Validate and normalize a quantity field."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, True

    if parsed <= 0:
        return None, True
    return parsed, False


def _validate_purchase_request(body: dict):
    """Validate a purchase request body before using the database."""
    product_id = body.get("productId")
    quantity = body.get("quantity", 1)
    if not product_id:
        return None, None, ({"detail": "productId is required"}, 400)

    try:
        parsed_product_id = int(product_id)
    except (TypeError, ValueError):
        return None, None, ({"detail": "productId is required"}, 400)

    quantity_value, quantity_error = _parse_quantity(quantity)
    if quantity_error:
        return None, None, (
            {"detail": "Quantity must be a positive whole number"},
            400,
        )

    return parsed_product_id, quantity_value, None


def _now_iso() -> str:
    """Return a UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()
