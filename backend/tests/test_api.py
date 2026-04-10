"""API tests for the SQLite-backed backend."""

from __future__ import annotations

from pathlib import Path

from backend.database import get_connection, reset_database
from backend.main import create_app


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_client(tmp_path: Path):
    database_path = tmp_path / "test_team21.db"
    reset_database(database_path)
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database_path),
        }
    )
    return app.test_client(), str(database_path)


def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/api/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.get_json()["token"]


def _count_rows(database_path: str, table_name: str) -> int:
    with get_connection(database_path) as connection:
        row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {table_name}"
        ).fetchone()
    return row["count"]


def test_health_endpoint(tmp_path: Path):
    """Health endpoint should report the backend is up."""
    client, _ = _make_client(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_swagger_ui_is_available(tmp_path: Path):
    """Swagger UI should be exposed for runtime API testing."""
    client, _ = _make_client(tmp_path)

    response = client.get("/apidocs/")

    assert response.status_code == 200


def test_register_then_login_persists_user_to_database(tmp_path: Path):
    """Registering should create a SQLite row that can then log in."""
    client, database_path = _make_client(tmp_path)

    register_response = client.post(
        "/api/register",
        json={
            "email": "newbuyer@example.com",
            "password": "testpass",
            "role": "buyer",
        },
    )
    login_response = client.post(
        "/api/login",
        json={"email": "newbuyer@example.com", "password": "testpass"},
    )

    with get_connection(database_path) as connection:
        user = connection.execute(
            "SELECT email, role FROM users WHERE email = ?",
            ("newbuyer@example.com",),
        ).fetchone()

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    assert user["email"] == "newbuyer@example.com"
    assert user["role"] == "buyer"


def test_register_rejects_duplicate_email_without_creating_user(tmp_path: Path):
    """Register should reject duplicate emails and leave the database unchanged."""
    client, database_path = _make_client(tmp_path)
    starting_count = _count_rows(database_path, "users")

    response = client.post(
        "/api/register",
        json={
            "email": "buyer@example.com",
            "password": "anotherpass",
            "role": "buyer",
        },
    )

    assert response.status_code == 409
    assert response.get_json()["detail"] == "Email already registered"
    assert _count_rows(database_path, "users") == starting_count


def test_login_rejects_wrong_password(tmp_path: Path):
    """Login should fail cleanly when credentials are incorrect."""
    client, _ = _make_client(tmp_path)

    response = client.post(
        "/api/login",
        json={"email": "buyer@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert response.get_json()["detail"] == "Invalid email or password"


def test_protected_route_requires_bearer_token(tmp_path: Path):
    """Protected routes should reject requests without a bearer token."""
    client, _ = _make_client(tmp_path)

    response = client.post(
        "/api/products",
        json={"title": "Tomatoes", "price": 3.5},
    )

    assert response.status_code == 401
    assert response.get_json()["detail"] == "Missing bearer token"


def test_protected_route_rejects_invalid_bearer_token(tmp_path: Path):
    """Protected routes should reject tokens that do not map to a real user."""
    client, _ = _make_client(tmp_path)

    response = client.post(
        "/api/products",
        json={"title": "Tomatoes", "price": 3.5},
        headers={"Authorization": "Bearer definitely-not-valid"},
    )

    assert response.status_code == 401
    assert response.get_json()["detail"] == "Invalid token"


def test_seller_can_create_product_and_db_row_is_saved(tmp_path: Path):
    """Seller product creation should insert a row into SQLite."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "seller@example.com", "sellerpass")

    response = client.post(
        "/api/products",
        json={
            "title": "Fresh Lettuce",
            "description": "Crisp and green.",
            "price": 4.25,
            "quantity": 8,
            "image_url": "/fruits/orange1.png",
        },
        headers=_auth_headers(token),
    )

    with get_connection(database_path) as connection:
        product = connection.execute(
            """
            SELECT title, price, quantity_available
            FROM products
            WHERE title = ?
            """,
            ("Fresh Lettuce",),
        ).fetchone()

    assert response.status_code == 201
    assert response.get_json()["message"] == "Product created"
    assert product["title"] == "Fresh Lettuce"
    assert product["price"] == 4.25
    assert product["quantity_available"] == 8


def test_create_product_rejects_negative_price(tmp_path: Path):
    """Product creation should reject invalid boundary input."""
    client, _ = _make_client(tmp_path)
    token = _login(client, "seller@example.com", "sellerpass")

    response = client.post(
        "/api/products",
        json={
            "title": "Bad Product",
            "description": "Should fail.",
            "price": -1,
            "quantity": 4,
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 400
    assert response.get_json()["detail"] == "Title and price are required"


def test_buyer_cannot_create_product(tmp_path: Path):
    """Only sellers should be able to create listings."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "buyer@example.com", "buyerpass")
    starting_count = _count_rows(database_path, "products")

    response = client.post(
        "/api/products",
        json={
            "title": "Unauthorized Listing",
            "description": "Should not exist",
            "price": 4.0,
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.get_json()["detail"] == "Only sellers can create products"
    assert _count_rows(database_path, "products") == starting_count


def test_seller_can_update_own_product_in_database(tmp_path: Path):
    """Updating should modify the stored SQLite row."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "seller@example.com", "sellerpass")

    response = client.put(
        "/api/products/1",
        json={
            "title": "Fresh Strawberries Deluxe",
            "description": "Updated description",
            "price": 7.25,
            "quantity": 15,
            "image_url": "/fruits/apple2.png",
        },
        headers=_auth_headers(token),
    )

    with get_connection(database_path) as connection:
        product = connection.execute(
            """
            SELECT title, price, quantity_available, image_path
            FROM products
            WHERE id = 1
            """
        ).fetchone()

    assert response.status_code == 200
    assert product["title"] == "Fresh Strawberries Deluxe"
    assert product["price"] == 7.25
    assert product["quantity_available"] == 15
    assert product["image_path"] == "/fruits/apple2.png"


def test_update_product_rejects_quantity_below_reserved_inventory(tmp_path: Path):
    """Quantity updates should not drop below already reserved stock."""
    client, database_path = _make_client(tmp_path)
    buyer_token = _login(client, "buyer@example.com", "buyerpass")
    seller_token = _login(client, "seller@example.com", "sellerpass")

    purchase_response = client.post(
        "/api/purchases",
        json={"productId": 2, "quantity": 3},
        headers=_auth_headers(buyer_token),
    )
    assert purchase_response.status_code == 201

    response = client.put(
        "/api/products/2",
        json={"quantity": 2},
        headers=_auth_headers(seller_token),
    )

    with get_connection(database_path) as connection:
        product = connection.execute(
            """
            SELECT quantity_available, quantity_reserved
            FROM products
            WHERE id = 2
            """
        ).fetchone()

    assert response.status_code == 400
    assert response.get_json()["detail"] == (
        "Quantity cannot be lower than the reserved inventory"
    )
    assert product["quantity_available"] == 10
    assert product["quantity_reserved"] == 3


def test_seller_can_delete_own_product_from_database(tmp_path: Path):
    """Deleting a product should remove its row from SQLite."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "seller@example.com", "sellerpass")

    response = client.delete(
        "/api/products/2",
        headers=_auth_headers(token),
    )

    with get_connection(database_path) as connection:
        product = connection.execute(
            "SELECT id FROM products WHERE id = 2"
        ).fetchone()

    assert response.status_code == 200
    assert response.get_json()["message"] == "Product deleted"
    assert product is None


def test_purchase_creates_pending_order_and_reserves_inventory(tmp_path: Path):
    """Buying a product should create order rows and reserve inventory."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "buyer@example.com", "buyerpass")

    purchase_response = client.post(
        "/api/purchases",
        json={"productId": 2, "quantity": 3},
        headers=_auth_headers(token),
    )

    with get_connection(database_path) as connection:
        order = connection.execute(
            """
            SELECT id, buyer_id, seller_id, status
            FROM orders
            WHERE id = ?
            """,
            (purchase_response.get_json()["orderId"],),
        ).fetchone()
        item = connection.execute(
            """
            SELECT quantity, unit_price
            FROM order_items
            WHERE order_id = ?
            """,
            (purchase_response.get_json()["orderId"],),
        ).fetchone()
        product = connection.execute(
            """
            SELECT quantity_available, quantity_reserved
            FROM products
            WHERE id = 2
            """
        ).fetchone()

    assert purchase_response.status_code == 201
    assert order["buyer_id"] == 1
    assert order["seller_id"] == 2
    assert order["status"] == "pending"
    assert item["quantity"] == 3
    assert item["unit_price"] == 5.0
    assert product["quantity_available"] == 10
    assert product["quantity_reserved"] == 3


def test_purchase_rejects_when_inventory_is_not_available(tmp_path: Path):
    """Purchases should fail once the requested quantity exceeds remaining inventory."""
    client, _ = _make_client(tmp_path)
    token = _login(client, "buyer@example.com", "buyerpass")

    response = client.post(
        "/api/purchases",
        json={"productId": 2, "quantity": 99},
        headers=_auth_headers(token),
    )

    assert response.status_code == 409
    assert response.get_json()["detail"] == "Not enough inventory available"


def test_purchase_rejects_missing_product_id(tmp_path: Path):
    """Purchase requests need a product id."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "buyer@example.com", "buyerpass")
    starting_orders = _count_rows(database_path, "orders")

    response = client.post(
        "/api/purchases",
        json={"quantity": 1},
        headers=_auth_headers(token),
    )

    assert response.status_code == 400
    assert response.get_json()["detail"] == "productId is required"
    assert _count_rows(database_path, "orders") == starting_orders


def test_purchase_rejects_non_positive_quantity(tmp_path: Path):
    """Purchase quantity must be a positive whole number."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "buyer@example.com", "buyerpass")
    starting_orders = _count_rows(database_path, "orders")
    starting_items = _count_rows(database_path, "order_items")

    response = client.post(
        "/api/purchases",
        json={"productId": 2, "quantity": 0},
        headers=_auth_headers(token),
    )

    assert response.status_code == 400
    assert response.get_json()["detail"] == (
        "Quantity must be a positive whole number"
    )
    assert _count_rows(database_path, "orders") == starting_orders
    assert _count_rows(database_path, "order_items") == starting_items


def test_seller_cannot_create_purchase(tmp_path: Path):
    """Only buyers should be allowed to create purchases."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "seller@example.com", "sellerpass")
    starting_orders = _count_rows(database_path, "orders")

    response = client.post(
        "/api/purchases",
        json={"productId": 1, "quantity": 1},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.get_json()["detail"] == "Only buyers can purchase products"
    assert _count_rows(database_path, "orders") == starting_orders


def test_buyer_can_send_and_fetch_messages_from_database(tmp_path: Path):
    """Message creation should persist and later be returned by the API."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "buyer@example.com", "buyerpass")

    send_response = client.post(
        "/api/messages",
        json={"productId": 2, "content": "Can I pick this up tomorrow?"},
        headers=_auth_headers(token),
    )
    fetch_response = client.get(
        "/api/messages?productId=2",
        headers=_auth_headers(token),
    )

    with get_connection(database_path) as connection:
        stored_message = connection.execute(
            """
            SELECT content, buyer_id, seller_id
            FROM messages
            WHERE id = ?
            """,
            (send_response.get_json()["messageId"],),
        ).fetchone()

    assert send_response.status_code == 201
    assert fetch_response.status_code == 200
    assert len(fetch_response.get_json()) == 1
    assert stored_message["content"] == "Can I pick this up tomorrow?"
    assert stored_message["buyer_id"] == 1
    assert stored_message["seller_id"] == 2


def test_seller_cannot_start_a_new_product_conversation(tmp_path: Path):
    """The first message for a product must come from a buyer."""
    client, database_path = _make_client(tmp_path)
    token = _login(client, "seller@example.com", "sellerpass")
    starting_count = _count_rows(database_path, "messages")

    response = client.post(
        "/api/messages",
        json={"productId": 2, "content": "Pickup starts at 9 AM."},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403
    assert response.get_json()["detail"] == "The first message must be sent by a buyer"
    assert _count_rows(database_path, "messages") == starting_count


def test_messages_require_a_product_id(tmp_path: Path):
    """Message fetches should reject missing required query parameters."""
    client, _ = _make_client(tmp_path)
    token = _login(client, "buyer@example.com", "buyerpass")

    response = client.get(
        "/api/messages",
        headers=_auth_headers(token),
    )

    assert response.status_code == 400
    assert response.get_json()["detail"] == "productId is required"
