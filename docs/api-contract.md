# API Contract

This document describes the milestone 5 API stubs for the Local Farm Marketplace project. These routes use mock in-memory data and do not connect to a real database.

## Base URL

`http://localhost:8000`

## Authentication

Protected routes expect this header:

`Authorization: Bearer <token>`

The token is returned from the login route.

## Endpoints

### `GET /api/health`

Purpose: Confirm the backend is running.

Response:

```json
{
  "status": "ok",
  "message": "Flask backend is running!"
}
```

### `POST /api/register`

Purpose: Create a new mock user account.

Request body:

```json
{
  "email": "student@example.com",
  "password": "testpass",
  "role": "buyer"
}
```

Success response:

```json
{
  "message": "Registration successful",
  "userId": 3
}
```

### `POST /api/login`

Purpose: Log in with a mock user account.

Request body:

```json
{
  "email": "buyer@example.com",
  "password": "buyerpass"
}
```

Success response:

```json
{
  "message": "Login successful",
  "token": "mock-token-1-buyer",
  "role": "buyer",
  "email": "buyer@example.com",
  "userId": 1
}
```

### `GET /api/products`

Purpose: Return all mock products.

Optional query parameter:

`sort=default|price_asc|price_desc|popular`

Success response:

```json
[
  {
    "id": 1,
    "title": "Fresh Strawberries",
    "description": "Sweet strawberries picked this morning.",
    "price": 6.5,
    "image_url": "/fruits/apple1.png",
    "seller_id": 2,
    "purchase_count": 1
  }
]
```

### `POST /api/products`

Purpose: Create a product as a seller.

Request body:

```json
{
  "title": "Fresh Lettuce",
  "description": "Crisp and green.",
  "price": 4.25,
  "image_url": "/fruits/orange1.png"
}
```

Success response:

```json
{
  "message": "Product created",
  "productId": 3
}
```

### `PUT /api/products/<id>`

Purpose: Update a seller's own product.

Request body:

```json
{
  "title": "Fresh Lettuce",
  "description": "Updated description",
  "price": 4.5,
  "image_url": "/fruits/orange1.png"
}
```

Success response:

```json
{
  "message": "Product updated"
}
```

### `DELETE /api/products/<id>`

Purpose: Delete a seller's own product.

Success response:

```json
{
  "message": "Product deleted"
}
```

### `GET /api/messages?productId=<id>`

Purpose: Return messages for a product conversation.

Success response:

```json
[
  {
    "id": 1,
    "product_id": 1,
    "buyer_id": 1,
    "seller_id": 2,
    "sender_id": 1,
    "sender_role": "buyer",
    "sender_email": "buyer@example.com",
    "content": "Are these available for pickup today?",
    "created_at": "2026-04-03T09:00:00+00:00"
  }
]
```

### `POST /api/messages`

Purpose: Send a message about a product.

Request body:

```json
{
  "productId": 2,
  "content": "Can I pick this up tomorrow?"
}
```

Success response:

```json
{
  "message": "Message sent",
  "messageId": 2
}
```

### `POST /api/purchases`

Purpose: Create a mock purchase as a buyer.

Request body:

```json
{
  "productId": 2
}
```

Success response:

```json
{
  "message": "Purchase successful"
}
```
