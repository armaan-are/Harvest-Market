"""SQLite database helpers and seed data for the farm marketplace."""

from __future__ import annotations

import os
import hashlib
import hmac
import sqlite3
import secrets
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
DEFAULT_DB_PATH = DATA_DIR / "team21_market.db"
DB_PATH = Path(os.environ.get("TEAM21_DB_PATH", str(DEFAULT_DB_PATH)))


SCHEMA = [
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
    CREATE TABLE IF NOT EXISTS session_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
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


def now_iso() -> str:
    """Return a stable ISO timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    """Open a sqlite connection with row access by name."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def make_token(user_id: int, role: str) -> str:
    """Return a random bearer token for a logged-in session."""
    del user_id, role
    return f"team21-{secrets.token_urlsafe(32)}"


def hash_password(password: str) -> str:
    """Hash a password with a per-password salt."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_password: str) -> bool:
    """Verify a password hash, allowing legacy seed plaintext during upgrades."""
    if not stored_password.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(password, stored_password)

    try:
        _, salt, digest = stored_password.split("$", 2)
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()
    return hmac.compare_digest(candidate, digest)


def init_database() -> None:
    """Create the database if needed and seed it with sample data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for statement in SCHEMA:
            conn.execute(statement)

        row = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
        if row[0] == 0:
            seed_database(conn)
        conn.commit()


def reset_database() -> None:
    """Reset the sqlite database to a deterministic seeded state."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    if UPLOAD_DIR.exists():
        for path in UPLOAD_DIR.iterdir():
            if path.is_file():
                path.unlink()
    init_database()


def seed_database(conn: sqlite3.Connection) -> None:
    """Insert starter data for local runs and automated tests."""
    timestamp = "2026-04-03T08:00:00+00:00"

    conn.executemany(
        "INSERT INTO users (id, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "buyer@example.com", hash_password("buyerpass"), "buyer", timestamp),
            (2, "seller@example.com", hash_password("sellerpass"), "seller", timestamp),
            (3, "neighbor.jules@example.com", hash_password("buyerpass"), "buyer", timestamp),
            (4, "orchard.collective@example.com", hash_password("sellerpass"), "seller", timestamp),
        ],
    )
    conn.executemany(
        "INSERT INTO buyer_profiles (user_id, full_name, phone, home_zip) VALUES (?, ?, ?, ?)",
        [
            (1, "Default Buyer", "860-555-0101", "06269"),
            (3, "Jules Carter", "860-555-0147", "06268"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO farm_profiles (
            user_id, farm_name, biography, pickup_address, operating_hours, zip_code
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                2,
                "Team 21 Family Farm",
                "A small local farm serving the nearby community.",
                "123 Farm Lane, Storrs, CT",
                "Sat 9am-1pm",
                "06268",
            ),
            (
                4,
                "Orchard Collective",
                "Small-batch fruit, preserves, and pastries from a shared family orchard.",
                "88 Orchard Road, Mansfield, CT",
                "Fri 4pm-7pm, Sun 10am-1pm",
                "06250",
            ),
        ],
    )
    conn.executemany(
        "INSERT INTO categories (id, name) VALUES (?, ?)",
        [
            (1, "Produce"),
            (2, "Dairy"),
            (3, "Meat"),
            (4, "Baked Goods"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO products (
            id, seller_id, title, description, price, quantity_available,
            quantity_reserved, image_path, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                2,
                "Fresh Strawberries",
                "Sweet strawberries picked this morning.",
                6.5,
                9,
                0,
                "/fruits/apple1.png",
                timestamp,
                timestamp,
            ),
            (
                2,
                2,
                "Farm Eggs",
                "A dozen free-range eggs.",
                5.0,
                24,
                2,
                "/fruits/banana1.png",
                timestamp,
                timestamp,
            ),
            (
                3,
                2,
                "Heirloom Tomatoes",
                "Striped heirlooms with a bright, savory finish.",
                7.25,
                7,
                0,
                "/fruits/orange2.png",
                timestamp,
                timestamp,
            ),
            (
                4,
                2,
                "Rustic Sourdough",
                "Crackling crust and a soft center baked before sunrise.",
                8.75,
                5,
                0,
                "/fruits/apple4.png",
                timestamp,
                timestamp,
            ),
            (
                5,
                4,
                "Valencia Oranges",
                "Juicy orchard oranges packed for weekend pickup.",
                4.5,
                8,
                0,
                "/fruits/orange4.png",
                timestamp,
                timestamp,
            ),
            (
                6,
                4,
                "Cultured Butter",
                "Small-batch butter made with local cream.",
                6.25,
                14,
                0,
                "/fruits/banana4.png",
                timestamp,
                timestamp,
            ),
        ],
    )
    conn.executemany(
        "INSERT INTO product_categories (product_id, category_id) VALUES (?, ?)",
        [(1, 1), (2, 2), (3, 1), (4, 4), (5, 1), (6, 2)],
    )
    conn.executemany(
        """
        INSERT INTO orders (
            id, buyer_id, seller_id, status, pickup_window, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                1,
                2,
                "completed",
                "2026-04-03 10:00",
                "2026-04-03T08:30:00+00:00",
                "2026-04-03T11:00:00+00:00",
            ),
            (
                2,
                1,
                2,
                "pending",
                "2026-04-24 10:30",
                "2026-04-24T12:00:00+00:00",
                "2026-04-24T12:00:00+00:00",
            ),
            (
                3,
                3,
                2,
                "confirmed",
                "2026-04-24 13:00",
                "2026-04-23T14:00:00+00:00",
                "2026-04-23T15:30:00+00:00",
            ),
            (
                4,
                3,
                2,
                "ready_for_pickup",
                "2026-04-24 16:00",
                "2026-04-23T08:00:00+00:00",
                "2026-04-24T08:15:00+00:00",
            ),
            (
                5,
                1,
                2,
                "rejected",
                "2026-04-20 09:30",
                "2026-04-20T08:00:00+00:00",
                "2026-04-20T08:45:00+00:00",
            ),
            (
                6,
                3,
                2,
                "completed",
                "2026-04-18 11:00",
                "2026-04-18T09:00:00+00:00",
                "2026-04-18T12:30:00+00:00",
            ),
            (
                7,
                1,
                4,
                "completed",
                "2026-04-17 15:00",
                "2026-04-17T10:15:00+00:00",
                "2026-04-17T15:25:00+00:00",
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1, 1, 1, 6.5),
            (2, 2, 2, 5.0),
            (3, 3, 1, 7.25),
            (4, 4, 1, 8.75),
            (5, 2, 1, 5.0),
            (6, 3, 2, 7.25),
            (7, 5, 1, 4.5),
        ],
    )
    conn.executemany(
        """
        INSERT INTO messages (
            id, product_id, order_id, buyer_id, seller_id, sender_id, content, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                1,
                1,
                1,
                2,
                1,
                "Are these available for pickup today?",
                "2026-04-03T09:00:00+00:00",
            ),
            (
                2,
                2,
                2,
                1,
                2,
                1,
                "Could you hold two cartons until late morning?",
                "2026-04-24T12:05:00+00:00",
            ),
            (
                3,
                2,
                2,
                1,
                2,
                2,
                "Yes, I can have them packed by 10:30.",
                "2026-04-24T12:10:00+00:00",
            ),
            (
                4,
                3,
                3,
                3,
                2,
                3,
                "Do the tomatoes lean sweeter or more acidic this week?",
                "2026-04-23T14:10:00+00:00",
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO reviews (id, order_id, buyer_id, farmer_id, rating, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                6,
                3,
                2,
                5,
                "Great pickup and produce quality. The tomatoes were exactly as described.",
                "2026-04-18T13:00:00+00:00",
            ),
            (
                2,
                7,
                1,
                4,
                4,
                "Beautiful fruit and a very smooth handoff. I would order again.",
                "2026-04-17T16:00:00+00:00",
            ),
        ],
    )


def save_upload(file_storage) -> str:
    """Store an uploaded file and return the public path."""
    init_database()
    filename = Path(file_storage.filename or "").name
    stem = filename or "upload.bin"
    safe_name = f"{int(datetime.now(timezone.utc).timestamp())}_{stem}"
    target = UPLOAD_DIR / safe_name
    file_storage.save(target)
    return f"/uploads/{safe_name}"
