"""SQLite helpers and database initialization for the backend."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from backend import mock_state


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "team21_market.db"


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('buyer', 'seller')),
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS buyer_profiles (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        home_zip TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS farm_profiles (
        user_id INTEGER PRIMARY KEY,
        farm_name TEXT NOT NULL,
        biography TEXT NOT NULL,
        pickup_address TEXT NOT NULL,
        operating_hours TEXT NOT NULL,
        zip_code TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        seller_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        quantity_available INTEGER NOT NULL CHECK(quantity_available >= 0),
        quantity_reserved INTEGER NOT NULL DEFAULT 0 CHECK(quantity_reserved >= 0),
        image_path TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_categories (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
        UNIQUE(product_id, category_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        buyer_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(
            status IN (
                'pending', 'confirmed', 'ready_for_pickup',
                'completed', 'rejected', 'cancelled'
            )
        ),
        pickup_window TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price REAL NOT NULL CHECK(unit_price >= 0),
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        order_id INTEGER,
        buyer_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
        FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL UNIQUE,
        buyer_id INTEGER NOT NULL,
        farmer_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        comment TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
]


def resolve_database_path(database_path: str | Path | None = None) -> Path:
    """Return the configured database path."""
    if database_path is None:
        return DEFAULT_DB_PATH
    return Path(database_path)


def get_connection(database_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with row access enabled."""
    path = resolve_database_path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: str | Path | None = None) -> Path:
    """Create the schema and seed data if this is the first run."""
    path = resolve_database_path(database_path)
    with get_connection(path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _seed_database(connection)
        connection.commit()
    return path


def reset_database(database_path: str | Path | None = None) -> Path:
    """Delete and recreate the database for tests."""
    path = resolve_database_path(database_path)
    if path.exists():
        path.unlink()
    return initialize_database(path)


def _seed_database(connection: sqlite3.Connection) -> None:
    """Populate first-run data using the old mock state as the starter dataset."""
    existing_user = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing_user:
        return

    users = mock_state.INITIAL_STATE["users"]
    for user in users:
        connection.execute(
            """
            INSERT INTO users (id, email, password, role, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                user["email"],
                user["password"],
                user["role"],
                "2026-04-03T08:00:00+00:00",
            ),
        )

    insert_buyer_profile(
        connection,
        1,
        "Default Buyer",
        "860-555-0101",
        "06269",
    )
    insert_farm_profile(
        connection,
        2,
        {
            "farm_name": "Team 21 Family Farm",
            "biography": "A small local farm serving the nearby community.",
            "pickup_address": "123 Farm Lane, Storrs, CT",
            "operating_hours": "Sat 9am-1pm",
            "zip_code": "06268",
        },
    )

    categories = [
        (1, "Produce"),
        (2, "Dairy"),
        (3, "Meat"),
        (4, "Baked Goods"),
    ]
    connection.executemany(
        "INSERT INTO categories (id, name) VALUES (?, ?)",
        categories,
    )

    products = mock_state.INITIAL_STATE["products"]
    for product in products:
        connection.execute(
            """
            INSERT INTO products (
                id, seller_id, title, description, price, quantity_available,
                quantity_reserved, image_path, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["id"],
                product["seller_id"],
                product["title"],
                product["description"],
                product["price"],
                10,
                0,
                product["image_url"],
                "2026-04-03T08:00:00+00:00",
                "2026-04-03T08:00:00+00:00",
            ),
        )

    connection.executemany(
        """
        INSERT INTO product_categories (product_id, category_id)
        VALUES (?, ?)
        """,
        [
            (1, 1),
            (2, 2),
        ],
    )

    connection.execute(
        """
        INSERT INTO orders (
            id, buyer_id, seller_id, status, pickup_window, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            1,
            2,
            "completed",
            "2026-04-03 10:00",
            "2026-04-03T08:30:00+00:00",
            "2026-04-03T11:00:00+00:00",
        ),
    )
    connection.execute(
        """
        INSERT INTO order_items (id, order_id, product_id, quantity, unit_price)
        VALUES (?, ?, ?, ?, ?)
        """,
        (1, 1, 1, 1, 6.5),
    )

    messages = mock_state.INITIAL_STATE["messages"]
    for message in messages:
        connection.execute(
            """
            INSERT INTO messages (
                id, product_id, order_id, buyer_id, seller_id, sender_id, content, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message["id"],
                message["product_id"],
                1,
                message["buyer_id"],
                message["seller_id"],
                message["sender_id"],
                message["content"],
                message["created_at"],
            ),
        )


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a row object to a normal dictionary."""
    if row is None:
        return None
    return dict(row)


def insert_buyer_profile(
    connection: sqlite3.Connection,
    user_id: int,
    full_name: str,
    phone: str,
    home_zip: str,
) -> None:
    """Insert a buyer profile row."""
    connection.execute(
        """
        INSERT INTO buyer_profiles (user_id, full_name, phone, home_zip)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, full_name, phone, home_zip),
    )


def insert_farm_profile(
    connection: sqlite3.Connection,
    user_id: int,
    profile: dict,
) -> None:
    """Insert a farm profile row."""
    connection.execute(
        """
        INSERT INTO farm_profiles (
            user_id, farm_name, biography, pickup_address, operating_hours, zip_code
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            profile["farm_name"],
            profile["biography"],
            profile["pickup_address"],
            profile["operating_hours"],
            profile["zip_code"],
        ),
    )
