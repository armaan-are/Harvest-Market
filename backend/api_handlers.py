"""Small backend operations used by the Flask routes."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from backend.mock_state import STATE, find_product, find_user_by_email, make_token


def register_user(email: str, password: str, role: str):
    """Create a new mock user account."""
    if not email or not password or role not in {"buyer", "seller"}:
        return {"detail": "Missing or invalid registration fields"}, 400

    if find_user_by_email(email):
        return {"detail": "Email already registered"}, 409

    user = {
        "id": STATE["next_user_id"],
        "email": email,
        "password": password,
        "role": role,
    }
    STATE["next_user_id"] += 1
    STATE["users"].append(user)
    return {"message": "Registration successful", "userId": user["id"]}, 201


def login_user(email: str | None, password: str | None):
    """Log in and return a simple mock token."""
    user = find_user_by_email(email)
    if user is None or user["password"] != password:
        return {"detail": "Invalid email or password"}, 401

    return {
        "message": "Login successful",
        "token": make_token(user),
        "role": user["role"],
        "email": user["email"],
        "userId": user["id"],
    }, 200


def get_sorted_products(sort: str):
    """Return products, optionally sorted for the frontend."""
    products = deepcopy(STATE["products"])

    if sort == "price_asc":
        products.sort(key=lambda item: item["price"])
    elif sort == "price_desc":
        products.sort(key=lambda item: item["price"], reverse=True)
    elif sort == "popular":
        products.sort(
            key=lambda item: (item["purchase_count"], item["id"]),
            reverse=True,
        )
    else:
        products.sort(key=lambda item: item["id"], reverse=True)

    return products, 200


def create_product_record(current_user: dict, body: dict):
    """Create a product for a seller."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can create products"}, 403

    title = body.get("title")
    price = body.get("price")
    if not title or price is None:
        return {"detail": "Title and price are required"}, 400

    product = {
        "id": STATE["next_product_id"],
        "title": title,
        "description": body.get("description", ""),
        "price": float(price),
        "image_url": body.get("image_url", ""),
        "seller_id": current_user["id"],
        "purchase_count": 0,
    }
    STATE["next_product_id"] += 1
    STATE["products"].append(product)
    return {"message": "Product created", "productId": product["id"]}, 200


def update_product_record(current_user: dict, product_id: int, body: dict):
    """Update a seller's own product."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can update products"}, 403

    product = find_product(product_id)
    if product is None or product["seller_id"] != current_user["id"]:
        return {"detail": "You can only update your own products"}, 403

    product["title"] = body.get("title", product["title"])
    product["description"] = body.get("description", product["description"])
    product["price"] = float(body.get("price", product["price"]))
    product["image_url"] = body.get("image_url", product["image_url"])
    return {"message": "Product updated"}, 200


def delete_product_record(current_user: dict, product_id: int):
    """Delete a seller's own product."""
    if current_user["role"] != "seller":
        return {"detail": "Only sellers can delete products"}, 403

    product = find_product(product_id)
    if product is None or product["seller_id"] != current_user["id"]:
        return {"detail": "You can only delete your own products"}, 403

    STATE["products"] = [item for item in STATE["products"] if item["id"] != product_id]
    return {"message": "Product deleted"}, 200


def get_visible_messages(current_user: dict, product_id: int | None):
    """Return the messages a user can see for a product."""
    if product_id is None:
        return {"detail": "productId is required"}, 400

    visible_messages = [
        deepcopy(message)
        for message in STATE["messages"]
        if message["product_id"] == product_id
        and current_user["id"] in {message["buyer_id"], message["seller_id"]}
    ]
    return visible_messages, 200


def create_message_record(current_user: dict, body: dict):
    """Send a new mock message about a product."""
    product_id = body.get("productId")
    content = body.get("content")
    if not product_id or not content:
        return {"detail": "productId and content are required"}, 400

    product = find_product(int(product_id))
    if product is None:
        return {"detail": "Product not found"}, 404

    existing_messages = [
        message
        for message in STATE["messages"]
        if message["product_id"] == product["id"]
    ]
    if existing_messages:
        buyer_id = existing_messages[0]["buyer_id"]
        if current_user["id"] not in {buyer_id, product["seller_id"]}:
            return {"detail": "You are not part of this conversation"}, 403
    else:
        if current_user["role"] != "buyer":
            return {"detail": "The first message must be sent by a buyer"}, 403
        buyer_id = current_user["id"]

    message = {
        "id": STATE["next_message_id"],
        "product_id": product["id"],
        "buyer_id": buyer_id,
        "seller_id": product["seller_id"],
        "sender_id": current_user["id"],
        "sender_role": current_user["role"],
        "sender_email": current_user["email"],
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    STATE["next_message_id"] += 1
    STATE["messages"].append(message)
    return {"message": "Message sent", "messageId": message["id"]}, 201


def create_purchase_record(current_user: dict, body: dict):
    """Create a purchase for a buyer and update popularity."""
    if current_user["role"] != "buyer":
        return {"detail": "Only buyers can purchase products"}, 403

    product_id = body.get("productId")
    if not product_id:
        return {"detail": "productId is required"}, 400

    product = find_product(int(product_id))
    if product is None:
        return {"detail": "Product not found"}, 404

    purchase = {
        "id": STATE["next_purchase_id"],
        "buyer_id": current_user["id"],
        "seller_id": product["seller_id"],
        "product_id": product["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    STATE["next_purchase_id"] += 1
    STATE["purchases"].append(purchase)
    product["purchase_count"] += 1
    return {"message": "Purchase successful"}, 201
