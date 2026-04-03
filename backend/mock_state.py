"""Mock data and shared helpers for the milestone 5 backend."""

from __future__ import annotations

from copy import deepcopy


INITIAL_STATE = {
    "next_user_id": 3,
    "next_product_id": 3,
    "next_message_id": 2,
    "next_purchase_id": 2,
    "users": [
        {
            "id": 1,
            "email": "buyer@example.com",
            "password": "buyerpass",
            "role": "buyer",
        },
        {
            "id": 2,
            "email": "seller@example.com",
            "password": "sellerpass",
            "role": "seller",
        },
    ],
    "products": [
        {
            "id": 1,
            "title": "Fresh Strawberries",
            "description": "Sweet strawberries picked this morning.",
            "price": 6.5,
            "image_url": "/fruits/apple1.png",
            "seller_id": 2,
            "purchase_count": 1,
        },
        {
            "id": 2,
            "title": "Farm Eggs",
            "description": "A dozen free-range eggs.",
            "price": 5.0,
            "image_url": "/fruits/banana1.png",
            "seller_id": 2,
            "purchase_count": 0,
        },
    ],
    "messages": [
        {
            "id": 1,
            "product_id": 1,
            "buyer_id": 1,
            "seller_id": 2,
            "sender_id": 1,
            "sender_role": "buyer",
            "sender_email": "buyer@example.com",
            "content": "Are these available for pickup today?",
            "created_at": "2026-04-03T09:00:00+00:00",
        }
    ],
    "purchases": [
        {
            "id": 1,
            "buyer_id": 1,
            "seller_id": 2,
            "product_id": 1,
            "created_at": "2026-04-03T08:30:00+00:00",
        }
    ],
}

STATE = deepcopy(INITIAL_STATE)


def reset_mock_state() -> None:
    """Reset in-memory data so tests start from a clean known state."""
    STATE.clear()
    STATE.update(deepcopy(INITIAL_STATE))


def find_user_by_email(email: str | None):
    """Find a user by email in the in-memory store."""
    if email is None:
        return None
    for user in STATE["users"]:
        if user["email"] == email:
            return user
    return None


def find_product(product_id: int):
    """Find a product by id in the in-memory store."""
    for product in STATE["products"]:
        if product["id"] == product_id:
            return product
    return None


def make_token(user: dict) -> str:
    """Build a predictable token for the mock app."""
    return f"mock-token-{user['id']}-{user['role']}"
