"""Basic API tests for milestone 5."""

from backend.main import create_app, reset_mock_state


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint():
    """Health endpoint should report the backend is up."""
    reset_mock_state()
    client = create_app().test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_register_then_login():
    """A new user should be able to register and then log in."""
    reset_mock_state()
    client = create_app().test_client()

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

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    assert "token" in login_response.get_json()


def test_seller_can_create_product():
    """Seller should be able to create a new product."""
    reset_mock_state()
    client = create_app().test_client()
    login_response = client.post(
        "/api/login",
        json={"email": "seller@example.com", "password": "sellerpass"},
    )
    token = login_response.get_json()["token"]

    response = client.post(
        "/api/products",
        json={
            "title": "Fresh Lettuce",
            "description": "Crisp and green.",
            "price": 4.25,
            "image_url": "/fruits/orange1.png",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Product created"


def test_products_endpoint_returns_sorted_products():
    """Products endpoint should return items in the requested sort order."""
    reset_mock_state()
    client = create_app().test_client()

    response = client.get("/api/products?sort=price_asc")
    products = response.get_json()

    assert response.status_code == 200
    assert len(products) >= 2
    assert products[0]["price"] <= products[1]["price"]


def test_seller_can_update_own_product():
    """Seller should be able to update a product through the API."""
    reset_mock_state()
    client = create_app().test_client()
    login_response = client.post(
        "/api/login",
        json={"email": "seller@example.com", "password": "sellerpass"},
    )
    token = login_response.get_json()["token"]

    response = client.put(
        "/api/products/1",
        json={
            "title": "Fresh Strawberries Deluxe",
            "description": "Updated description",
            "price": 7.25,
            "image_url": "/fruits/apple2.png",
        },
        headers=_auth_headers(token),
    )
    products_response = client.get("/api/products")
    products = products_response.get_json()

    assert response.status_code == 200
    assert response.get_json()["message"] == "Product updated"
    assert any(
        product["id"] == 1
        and product["title"] == "Fresh Strawberries Deluxe"
        and product["price"] == 7.25
        for product in products
    )


def test_seller_can_delete_own_product():
    """Seller should be able to delete a product through the API."""
    reset_mock_state()
    client = create_app().test_client()
    login_response = client.post(
        "/api/login",
        json={"email": "seller@example.com", "password": "sellerpass"},
    )
    token = login_response.get_json()["token"]

    response = client.delete(
        "/api/products/2",
        headers=_auth_headers(token),
    )
    products_response = client.get("/api/products")
    products = products_response.get_json()

    assert response.status_code == 200
    assert response.get_json()["message"] == "Product deleted"
    assert all(product["id"] != 2 for product in products)


def test_buyer_can_purchase_and_popularity_updates():
    """Purchasing a product should increment its purchase count."""
    reset_mock_state()
    client = create_app().test_client()
    login_response = client.post(
        "/api/login",
        json={"email": "buyer@example.com", "password": "buyerpass"},
    )
    token = login_response.get_json()["token"]

    purchase_response = client.post(
        "/api/purchases",
        json={"productId": 2},
        headers=_auth_headers(token),
    )
    products_response = client.get("/api/products?sort=popular")
    products = products_response.get_json()

    assert purchase_response.status_code == 201
    assert products[0]["purchase_count"] >= products[1]["purchase_count"]


def test_buyer_can_send_and_fetch_messages():
    """Buyer should be able to send a message and fetch the conversation."""
    reset_mock_state()
    client = create_app().test_client()
    login_response = client.post(
        "/api/login",
        json={"email": "buyer@example.com", "password": "buyerpass"},
    )
    token = login_response.get_json()["token"]

    send_response = client.post(
        "/api/messages",
        json={"productId": 2, "content": "Can I pick this up tomorrow?"},
        headers=_auth_headers(token),
    )
    fetch_response = client.get(
        "/api/messages?productId=2",
        headers=_auth_headers(token),
    )

    assert send_response.status_code == 201
    assert fetch_response.status_code == 200
    assert len(fetch_response.get_json()) == 1
