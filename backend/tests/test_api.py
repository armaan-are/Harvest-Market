"""API tests for the SQLite-backed marketplace backend."""

from backend.main import create_app, reset_mock_state


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _login(client, email: str, password: str) -> str:
    response = client.post("/api/login", json={"email": email, "password": password})
    return response.get_json()["token"]


def test_health_endpoint():
    """Health endpoint should report the backend is up."""
    reset_mock_state()
    client = create_app().test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_swagger_docs_are_enabled():
    """Swagger UI should be available for API exploration."""
    reset_mock_state()
    client = create_app().test_client()

    response = client.get("/apidocs/")
    spec_response = client.get("/apispec_1.json")
    spec = spec_response.get_json()

    assert response.status_code == 200
    assert spec_response.status_code == 200
    assert spec["paths"]["/api/products"]["get"]["summary"] == "List products with sorting and filters"


def test_register_then_login_creates_profile():
    """Registering a user should create a matching empty profile."""
    reset_mock_state()
    client = create_app().test_client()

    register_response = client.post(
        "/api/register",
        json={"email": "newbuyer@example.com", "password": "testpass", "role": "buyer"},
    )
    login_response = client.post(
        "/api/login",
        json={"email": "newbuyer@example.com", "password": "testpass"},
    )
    token = login_response.get_json()["token"]
    profile_response = client.get("/api/profile", headers=_auth_headers(token))

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    assert profile_response.status_code == 200
    assert profile_response.get_json()["role"] == "buyer"


def test_seller_can_create_product_with_category_and_quantity():
    """Sellers should be able to create categorized inventory with quantity."""
    reset_mock_state()
    client = create_app().test_client()
    token = _login(client, "seller@example.com", "sellerpass")

    response = client.post(
        "/api/products",
        json={
            "title": "Fresh Lettuce",
            "description": "Crisp and green.",
            "price": 4.25,
            "quantity_available": 12,
            "category": "produce",
            "image_url": "/fruits/orange1.png",
        },
        headers=_auth_headers(token),
    )
    products_response = client.get("/api/products?category=produce")

    assert response.status_code == 200
    assert any(product["title"] == "Fresh Lettuce" for product in products_response.get_json())


def test_products_endpoint_supports_zip_filter():
    """Marketplace inventory should filter by farm zip code."""
    reset_mock_state()
    client = create_app().test_client()

    response = client.get("/api/products?zipCode=06268")

    assert response.status_code == 200
    assert len(response.get_json()) >= 1


def test_buyer_order_lifecycle_updates_inventory():
    """Confirming a pending order should reserve then deduct inventory."""
    reset_mock_state()
    client = create_app().test_client()
    buyer_token = _login(client, "buyer@example.com", "buyerpass")
    seller_token = _login(client, "seller@example.com", "sellerpass")
    before_products = client.get("/api/products")
    before_eggs = next(product for product in before_products.get_json() if product["id"] == 2)

    create_response = client.post(
        "/api/orders",
        json={"productId": 2, "quantity": 2, "pickupWindow": "Saturday 10:00"},
        headers=_auth_headers(buyer_token),
    )
    pending_orders = client.get("/api/orders?status=pending", headers=_auth_headers(seller_token))
    order_id = create_response.get_json()["orderId"]
    confirm_response = client.put(
        f"/api/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=_auth_headers(seller_token),
    )
    products_response = client.get("/api/products?sort=popular")
    products = products_response.get_json()

    assert create_response.status_code == 201
    assert pending_orders.status_code == 200
    assert confirm_response.status_code == 200
    eggs = next(product for product in products if product["id"] == 2)
    assert eggs["quantity_available"] == before_eggs["quantity_available"] - 2
    assert eggs["quantity_reserved"] == before_eggs["quantity_reserved"]


def test_buyer_can_cancel_pending_order():
    """Buyers should be able to cancel their own pending orders."""
    reset_mock_state()
    client = create_app().test_client()
    buyer_token = _login(client, "buyer@example.com", "buyerpass")

    create_response = client.post(
        "/api/orders",
        json={"productId": 2, "quantity": 1},
        headers=_auth_headers(buyer_token),
    )
    order_id = create_response.get_json()["orderId"]
    cancel_response = client.put(
        f"/api/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=_auth_headers(buyer_token),
    )

    assert cancel_response.status_code == 200


def test_buyer_can_send_and_fetch_messages():
    """Product-linked messaging should work for the buyer side."""
    reset_mock_state()
    client = create_app().test_client()
    token = _login(client, "buyer@example.com", "buyerpass")

    send_response = client.post(
        "/api/messages",
        json={"productId": 2, "content": "Can I pick this up tomorrow?"},
        headers=_auth_headers(token),
    )
    fetch_response = client.get("/api/messages?productId=2", headers=_auth_headers(token))

    assert send_response.status_code == 201
    assert fetch_response.status_code == 200
    assert any(
        message["content"] == "Can I pick this up tomorrow?"
        for message in fetch_response.get_json()
    )


def test_buyer_can_update_profile():
    """Buyers should be able to save and fetch their profile."""
    reset_mock_state()
    client = create_app().test_client()
    token = _login(client, "buyer@example.com", "buyerpass")

    update_response = client.put(
        "/api/profile",
        json={"full_name": "Finn Harrison", "phone": "860-111-2222", "home_zip": "06032"},
        headers=_auth_headers(token),
    )
    fetch_response = client.get("/api/profile", headers=_auth_headers(token))

    assert update_response.status_code == 200
    assert update_response.get_json()["home_zip"] == "06032"
    assert fetch_response.get_json()["home_zip"] == "06032"


def test_buyer_can_submit_review_only_after_completion():
    """Completed orders should unlock verified buyer reviews."""
    reset_mock_state()
    client = create_app().test_client()
    token = _login(client, "buyer@example.com", "buyerpass")
    before_count = len(client.get("/api/reviews").get_json())

    response = client.post(
        "/api/reviews",
        json={
            "orderId": 1,
            "rating": 5,
            "comment": "Great pickup and produce quality.",
        },
        headers=_auth_headers(token),
    )
    reviews_response = client.get("/api/reviews")

    assert response.status_code == 201
    assert len(reviews_response.get_json()) == before_count + 1
    assert any(review["order_id"] == 1 for review in reviews_response.get_json())


def test_seller_can_complete_order_lifecycle():
    """Sellers should be able to move an order through all milestone states."""
    reset_mock_state()
    client = create_app().test_client()
    buyer_token = _login(client, "buyer@example.com", "buyerpass")
    seller_token = _login(client, "seller@example.com", "sellerpass")

    create_response = client.post(
        "/api/orders",
        json={"productId": 2, "quantity": 1, "pickupWindow": "Saturday 10:00"},
        headers=_auth_headers(buyer_token),
    )
    order_id = create_response.get_json()["orderId"]

    confirm_response = client.put(
        f"/api/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=_auth_headers(seller_token),
    )
    ready_response = client.put(
        f"/api/orders/{order_id}/status",
        json={"status": "ready_for_pickup"},
        headers=_auth_headers(seller_token),
    )
    complete_response = client.put(
        f"/api/orders/{order_id}/status",
        json={"status": "completed"},
        headers=_auth_headers(seller_token),
    )
    completed_orders = client.get(
        "/api/orders?status=completed",
        headers=_auth_headers(buyer_token),
    )

    assert confirm_response.status_code == 200
    assert ready_response.status_code == 200
    assert complete_response.status_code == 200
    assert any(order["id"] == order_id for order in completed_orders.get_json())
