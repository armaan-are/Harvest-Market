"""SQLite-backed backend operations used by the Flask routes."""

from __future__ import annotations

from sqlite3 import Connection

from backend.db import get_conn, make_token, now_iso


STATUS_FLOW = {
    "pending": {"confirmed", "rejected", "cancelled"},
    "confirmed": {"ready_for_pickup"},
    "ready_for_pickup": {"completed"},
    "completed": set(),
    "rejected": set(),
    "cancelled": set(),
}


def register_user(email: str, password: str, role: str):
    """Create a new user account with an empty profile."""
    if not email or not password or role not in {"buyer", "seller"}:
        return {"detail": "Missing or invalid registration fields"}, 400

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if existing:
            return {"detail": "Email already registered"}, 409

        cursor = conn.execute(
            """
            INSERT INTO users (email, password, role, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (email, password, role, now_iso()),
        )
        user_id = cursor.lastrowid

        if role == "buyer":
            conn.execute(
                """
                INSERT INTO buyer_profiles (user_id, full_name, phone, home_zip)
                VALUES (?, '', '', '')
                """,
                (user_id,),
            )
        else:
            conn.execute(
                """
                INSERT INTO farm_profiles (
                    user_id, farm_name, biography, pickup_address, operating_hours, zip_code
                ) VALUES (?, '', '', '', '', '')
                """,
                (user_id,),
            )

    return {"message": "Registration successful", "userId": user_id}, 201


def login_user(email: str | None, password: str | None):
    """Log in and return the bearer token."""
    if not email or not password:
        return {"detail": "Email and password are required"}, 400

    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, email, role, password FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if user is None or user["password"] != password:
        return {"detail": "Invalid email or password"}, 401

    return {
        "message": "Login successful",
        "token": make_token(user["id"], user["role"]),
        "role": user["role"],
        "email": user["email"],
        "userId": user["id"],
    }, 200


def get_user_from_token(token: str | None):
    """Resolve a user from the app's predictable bearer token."""
    if not token:
        return None

    with get_conn() as conn:
        users = conn.execute("SELECT id, email, role FROM users").fetchall()
        for user in users:
            if token == make_token(user["id"], user["role"]):
                return dict(user)
    return None


def get_categories():
    """Return the supported marketplace categories."""
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name FROM categories ORDER BY name").fetchall()
    return [dict(row) for row in rows], 200


def get_sorted_products(sort: str, category: str | None = None, zip_code: str | None = None):
    """Return products sorted and optionally filtered by category and farm zip."""
    order_by = {
        "price_asc": "p.price ASC, p.id DESC",
        "price_desc": "p.price DESC, p.id DESC",
        "popular": "purchase_count DESC, p.id DESC",
        "default": "p.id DESC",
    }.get(sort, "p.id DESC")

    clauses = []
    params: list[str] = []

    if category and category != "all":
        clauses.append("LOWER(c.name) = ?")
        params.append(category.replace("_", " ").lower())

    if zip_code:
        clauses.append("fp.zip_code = ?")
        params.append(zip_code)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT
                p.id,
                p.title,
                p.description,
                p.price,
                p.quantity_available,
                p.quantity_reserved,
                p.image_path,
                p.seller_id,
                COALESCE(fp.farm_name, u.email) AS farm_name,
                COALESCE(fp.zip_code, '') AS zip_code,
                LOWER(REPLACE(COALESCE(c.name, 'Produce'), ' ', '_')) AS category,
                COALESCE((
                    SELECT SUM(oi.quantity)
                    FROM order_items oi
                    JOIN orders o ON o.id = oi.order_id
                    WHERE oi.product_id = p.id
                      AND o.status IN ('confirmed', 'ready_for_pickup', 'completed')
                ), 0) AS purchase_count,
                COALESCE((
                    SELECT ROUND(AVG(r.rating), 2)
                    FROM reviews r
                    WHERE r.farmer_id = p.seller_id
                ), 0) AS average_rating
            FROM products p
            JOIN users u ON u.id = p.seller_id
            LEFT JOIN farm_profiles fp ON fp.user_id = p.seller_id
            LEFT JOIN product_categories pc ON pc.product_id = p.id
            LEFT JOIN categories c ON c.id = pc.category_id
            {where}
            ORDER BY {order_by}
            """,
            params,
        ).fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "price": row["price"],
            "quantity_available": row["quantity_available"],
            "quantity_reserved": row["quantity_reserved"],
            "image_url": row["image_path"],
            "seller_id": row["seller_id"],
            "purchase_count": row["purchase_count"],
            "farm_name": row["farm_name"],
            "zip_code": row["zip_code"],
            "category": row["category"],
            "average_rating": row["average_rating"],
        }
        for row in rows
    ], 200


def create_product_record(current_user: dict, body: dict):
    """Create a product for a seller."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can create products"}, 403

    validation = _validate_product_payload(body)
    if validation:
        return validation, 400

    category_id = _get_category_id(body.get("category"))
    timestamp = now_iso()

    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO products (
                seller_id, title, description, price, quantity_available,
                quantity_reserved, image_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                current_user["id"],
                body["title"].strip(),
                body.get("description", "").strip(),
                float(body["price"]),
                int(body.get("quantity_available", 1)),
                body.get("image_url") or "/fruits/apple1.png",
                timestamp,
                timestamp,
            ),
        )
        product_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO product_categories (product_id, category_id) VALUES (?, ?)",
            (product_id, category_id),
        )

    return {"message": "Product created", "productId": product_id}, 200


def update_product_record(current_user: dict, product_id: int, body: dict):
    """Update a seller's own product."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can update products"}, 403

    validation = _validate_product_payload(body)
    if validation:
        return validation, 400

    with get_conn() as conn:
        product = conn.execute(
            """
            SELECT id, seller_id, quantity_reserved
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()
        if product is None or product["seller_id"] != current_user["id"]:
            return {"detail": "You can only update your own products"}, 403

        new_quantity = int(body.get("quantity_available", 1))
        if new_quantity < product["quantity_reserved"]:
            return {"detail": "Quantity cannot be lower than reserved inventory"}, 400

        conn.execute(
            """
            UPDATE products
            SET title = ?, description = ?, price = ?, quantity_available = ?,
                image_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                body["title"].strip(),
                body.get("description", "").strip(),
                float(body["price"]),
                new_quantity,
                body.get("image_url") or "/fruits/apple1.png",
                now_iso(),
                product_id,
            ),
        )

        category_id = _get_category_id(body.get("category"))
        conn.execute("DELETE FROM product_categories WHERE product_id = ?", (product_id,))
        conn.execute(
            "INSERT INTO product_categories (product_id, category_id) VALUES (?, ?)",
            (product_id, category_id),
        )

    return {"message": "Product updated"}, 200


def delete_product_record(current_user: dict, product_id: int):
    """Delete a seller's own product."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can delete products"}, 403

    with get_conn() as conn:
        product = conn.execute(
            "SELECT seller_id FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if product is None or product["seller_id"] != current_user["id"]:
            return {"detail": "You can only delete your own products"}, 403

        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))

    return {"message": "Product deleted"}, 200


def get_visible_messages(current_user: dict, product_id: int | None):
    """Return messages for a product conversation."""
    if product_id is None:
        return {"detail": "productId is required"}, 400

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                m.id,
                m.product_id,
                m.order_id,
                m.buyer_id,
                m.seller_id,
                m.sender_id,
                sender.role AS sender_role,
                sender.email AS sender_email,
                m.content,
                m.created_at
            FROM messages m
            JOIN users sender ON sender.id = m.sender_id
            WHERE m.product_id = ?
              AND ? IN (m.buyer_id, m.seller_id)
            ORDER BY m.created_at ASC
            """,
            (product_id, current_user["id"]),
        ).fetchall()

    return [dict(row) for row in rows], 200


def create_message_record(current_user: dict, body: dict):
    """Create a product-linked message."""
    product_id = body.get("productId")
    content = (body.get("content") or "").strip()
    if not product_id or not content:
        return {"detail": "productId and content are required"}, 400

    with get_conn() as conn:
        product = conn.execute(
            "SELECT id, seller_id FROM products WHERE id = ?",
            (int(product_id),),
        ).fetchone()
        if product is None:
            return {"detail": "Product not found"}, 404

        existing = conn.execute(
            """
            SELECT buyer_id, seller_id
            FROM messages
            WHERE product_id = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (product["id"],),
        ).fetchone()

        if existing:
            buyer_id = existing["buyer_id"]
            if current_user["id"] not in {buyer_id, product["seller_id"]}:
                return {"detail": "You are not part of this conversation"}, 403
        else:
            if current_user["role"] != "buyer":
                return {"detail": "The first message must be sent by a buyer"}, 403
            buyer_id = current_user["id"]

        order = conn.execute(
            """
            SELECT id
            FROM orders
            WHERE buyer_id = ? AND seller_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (buyer_id, product["seller_id"]),
        ).fetchone()
        order_id = order["id"] if order else None

        cursor = conn.execute(
            """
            INSERT INTO messages (
                product_id, order_id, buyer_id, seller_id, sender_id, content, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["id"],
                order_id,
                buyer_id,
                product["seller_id"],
                current_user["id"],
                content,
                now_iso(),
            ),
        )

    return {"message": "Message sent", "messageId": cursor.lastrowid}, 201


def create_order_record(current_user: dict, body: dict):
    """Create a new pending order for a product."""
    if current_user["role"] != "buyer":
        return {"detail": "Only buyers can place orders"}, 403

    product_id = body.get("productId")
    quantity = int(body.get("quantity", 1))
    if not product_id or quantity <= 0:
        return {"detail": "productId and a positive quantity are required"}, 400

    with get_conn() as conn:
        product = conn.execute(
            """
            SELECT id, seller_id, price, quantity_available, quantity_reserved
            FROM products
            WHERE id = ?
            """,
            (int(product_id),),
        ).fetchone()
        if product is None:
            return {"detail": "Product not found"}, 404

        available_to_reserve = product["quantity_available"] - product["quantity_reserved"]
        if quantity > available_to_reserve:
            return {"detail": "Requested quantity exceeds available inventory"}, 400

        timestamp = now_iso()
        cursor = conn.execute(
            """
            INSERT INTO orders (
                buyer_id, seller_id, status, pickup_window, created_at, updated_at
            ) VALUES (?, ?, 'pending', ?, ?, ?)
            """,
            (
                current_user["id"],
                product["seller_id"],
                body.get("pickupWindow", ""),
                timestamp,
                timestamp,
            ),
        )
        order_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, product["id"], quantity, product["price"]),
        )
        conn.execute(
            """
            UPDATE products
            SET quantity_reserved = quantity_reserved + ?, updated_at = ?
            WHERE id = ?
            """,
            (quantity, timestamp, product["id"]),
        )

    return {"message": "Order request submitted", "orderId": order_id}, 201


def list_orders_for_user(current_user: dict, status: str | None = None):
    """Return buyer orders or seller requests for the current user."""
    clauses = [
        "o.buyer_id = ?" if current_user["role"] == "buyer" else "o.seller_id = ?"
    ]
    params: list[object] = [current_user["id"]]
    if status and status != "all":
        clauses.append("o.status = ?")
        params.append(status)

    where = " AND ".join(clauses)

    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT
                o.id,
                o.buyer_id,
                o.seller_id,
                o.status,
                o.pickup_window,
                o.created_at,
                o.updated_at,
                oi.product_id,
                oi.quantity,
                oi.unit_price,
                p.title AS product_title,
                p.image_path,
                buyer.email AS buyer_email,
                seller.email AS seller_email,
                COALESCE(fp.farm_name, seller.email) AS farm_name
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            JOIN products p ON p.id = oi.product_id
            JOIN users buyer ON buyer.id = o.buyer_id
            JOIN users seller ON seller.id = o.seller_id
            LEFT JOIN farm_profiles fp ON fp.user_id = o.seller_id
            WHERE {where}
            ORDER BY o.updated_at DESC, o.id DESC
            """,
            params,
        ).fetchall()

    return [
        {
            "id": row["id"],
            "buyer_id": row["buyer_id"],
            "seller_id": row["seller_id"],
            "status": row["status"],
            "pickup_window": row["pickup_window"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "product_id": row["product_id"],
            "product_title": row["product_title"],
            "image_url": row["image_path"],
            "quantity": row["quantity"],
            "unit_price": row["unit_price"],
            "total_price": round(row["quantity"] * row["unit_price"], 2),
            "buyer_email": row["buyer_email"],
            "seller_email": row["seller_email"],
            "farm_name": row["farm_name"],
        }
        for row in rows
    ], 200


def update_order_status_record(  # pylint: disable=too-many-return-statements
    current_user: dict, order_id: int, new_status: str
):
    """Advance or close an order and reconcile reserved inventory."""
    if new_status not in {
        "confirmed",
        "ready_for_pickup",
        "completed",
        "rejected",
        "cancelled",
    }:
        return {"detail": "Invalid status"}, 400

    with get_conn() as conn:
        order = _fetch_order_for_update(conn, order_id)
        if order is None:
            return {"detail": "Order not found"}, 404

        if current_user["role"] == "seller":
            if order["seller_id"] != current_user["id"]:
                return {"detail": "You can only manage your own incoming orders"}, 403
        else:
            if order["buyer_id"] != current_user["id"] or new_status != "cancelled":
                return {"detail": "Buyers can only cancel their own pending orders"}, 403
            if order["status"] != "pending":
                return {"detail": "Only pending orders can be cancelled"}, 400

        if new_status not in STATUS_FLOW[order["status"]]:
            return {"detail": "That order status transition is not allowed"}, 400

        timestamp = now_iso()
        quantity = order["quantity"]
        product_id = order["product_id"]

        if new_status == "confirmed":
            conn.execute(
                """
                UPDATE products
                SET quantity_available = quantity_available - ?,
                    quantity_reserved = quantity_reserved - ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (quantity, quantity, timestamp, product_id),
            )
        elif new_status in {"rejected", "cancelled"}:
            conn.execute(
                """
                UPDATE products
                SET quantity_reserved = quantity_reserved - ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (quantity, timestamp, product_id),
            )

        conn.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, timestamp, order_id),
        )

    return {"message": "Order updated"}, 200


def get_profile(current_user: dict):
    """Return the role-specific profile for the current user."""
    with get_conn() as conn:
        if current_user["role"] == "buyer":
            row = conn.execute(
                """
                SELECT full_name, phone, home_zip
                FROM buyer_profiles
                WHERE user_id = ?
                """,
                (current_user["id"],),
            ).fetchone()
            payload = dict(row or {})
        else:
            row = conn.execute(
                """
                SELECT farm_name, biography, pickup_address, operating_hours, zip_code
                FROM farm_profiles
                WHERE user_id = ?
                """,
                (current_user["id"],),
            ).fetchone()
            payload = dict(row or {})

    payload["role"] = current_user["role"]
    payload["email"] = current_user["email"]
    return payload, 200


def update_profile(current_user: dict, body: dict):
    """Update the role-specific profile for the current user."""
    with get_conn() as conn:
        if current_user["role"] == "buyer":
            conn.execute(
                """
                UPDATE buyer_profiles
                SET full_name = ?, phone = ?, home_zip = ?
                WHERE user_id = ?
                """,
                (
                    (body.get("full_name") or "").strip(),
                    (body.get("phone") or "").strip(),
                    (body.get("home_zip") or "").strip(),
                    current_user["id"],
                ),
            )
        else:
            conn.execute(
                """
                UPDATE farm_profiles
                SET farm_name = ?, biography = ?, pickup_address = ?,
                    operating_hours = ?, zip_code = ?
                WHERE user_id = ?
                """,
                (
                    (body.get("farm_name") or "").strip(),
                    (body.get("biography") or "").strip(),
                    (body.get("pickup_address") or "").strip(),
                    (body.get("operating_hours") or "").strip(),
                    (body.get("zip_code") or "").strip(),
                    current_user["id"],
                ),
            )

    return get_profile(current_user)


def list_reviews(farmer_id: int | None = None):
    """Return reviews, optionally scoped to a single farmer."""
    clauses = []
    params: list[object] = []
    if farmer_id:
        clauses.append("r.farmer_id = ?")
        params.append(farmer_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT
                r.id,
                r.order_id,
                r.buyer_id,
                r.farmer_id,
                r.rating,
                r.comment,
                r.created_at,
                buyer.email AS buyer_email,
                COALESCE(fp.farm_name, seller.email) AS farm_name
            FROM reviews r
            JOIN users buyer ON buyer.id = r.buyer_id
            JOIN users seller ON seller.id = r.farmer_id
            LEFT JOIN farm_profiles fp ON fp.user_id = r.farmer_id
            {where}
            ORDER BY r.created_at DESC
            """,
            params,
        ).fetchall()

    return [dict(row) for row in rows], 200


def create_review_record(current_user: dict, body: dict):
    """Create a verified review for a completed order."""
    if current_user["role"] != "buyer":
        return {"detail": "Only buyers can leave reviews"}, 403

    order_id = body.get("orderId")
    rating = int(body.get("rating", 0))
    comment = (body.get("comment") or "").strip()
    if not order_id or rating not in {1, 2, 3, 4, 5} or not comment:
        return {"detail": "orderId, rating, and comment are required"}, 400

    with get_conn() as conn:
        order = conn.execute(
            """
            SELECT id, buyer_id, seller_id, status
            FROM orders
            WHERE id = ?
            """,
            (int(order_id),),
        ).fetchone()
        if order is None or order["buyer_id"] != current_user["id"]:
            return {"detail": "Order not found"}, 404
        if order["status"] != "completed":
            return {"detail": "Reviews are only allowed after pickup is completed"}, 400

        existing = conn.execute(
            "SELECT id FROM reviews WHERE order_id = ?",
            (order["id"],),
        ).fetchone()
        if existing:
            return {"detail": "A review already exists for that order"}, 409

        cursor = conn.execute(
            """
            INSERT INTO reviews (order_id, buyer_id, farmer_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                order["id"],
                current_user["id"],
                order["seller_id"],
                rating,
                comment,
                now_iso(),
            ),
        )

    return {"message": "Review submitted", "reviewId": cursor.lastrowid}, 201


def _validate_product_payload(body: dict):
    title = (body.get("title") or "").strip()
    category = body.get("category") or "produce"
    try:
        price = float(body.get("price"))
        quantity = int(body.get("quantity_available", 1))
    except (TypeError, ValueError):
        return {"detail": "Price and quantity are required"}

    if not title:
        return {"detail": "Title is required"}
    if price < 0 or quantity < 0:
        return {"detail": "Price and quantity must be non-negative"}

    try:
        _get_category_id(category)
    except ValueError as error:
        return {"detail": str(error)}

    return None


def _get_category_id(category: str | None) -> int:
    normalized = (category or "produce").replace("_", " ").strip().lower()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM categories WHERE LOWER(name) = ?",
            (normalized,),
        ).fetchone()
    if row is None:
        raise ValueError("Invalid category")
    return row["id"]


def _fetch_order_for_update(conn: Connection, order_id: int):
    return conn.execute(
        """
        SELECT o.id, o.buyer_id, o.seller_id, o.status,
               oi.product_id, oi.quantity
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.id = ?
        """,
        (order_id,),
    ).fetchone()
