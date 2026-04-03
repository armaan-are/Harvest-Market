"""
Seed the database with a test user and sample products.
Run from project root: python -m backend.seed_db
"""
import sqlite3

from backend.db import SQLITE_PATH, _init_schema
from backend.auth import hash_password


def main():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    cur = conn.cursor()

    # Test users (password: test123)
    try:
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("seller@test.com", hash_password("test123"), "seller"),
        )
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("buyer@test.com", hash_password("test123"), "buyer"),
        )
    except sqlite3.IntegrityError:
        pass  # already seeded

    cur.execute("SELECT id FROM users WHERE role = 'seller' LIMIT 1")
    row = cur.fetchone()
    seller_id = row["id"] if row else 1

    # Sample products
    products = [
        ("Fresh Tomatoes", "Vine-ripened local tomatoes", 3.50, None),
        ("Organic Eggs", "Free-range, dozen", 5.00, None),
        ("Honey", "Local wildflower honey, 12 oz", 8.00, None),
        ("Apples", "Mixed variety, per lb", 2.25, None),
        ("Pumpkin", "Sugar pumpkin for pie", 4.00, None),
    ]
    for title, description, price, image_url in products:
        cur.execute(
            "SELECT 1 FROM products WHERE title = ? AND seller_id = ?",
            (title, seller_id),
        )
        if cur.fetchone():
            continue
        cur.execute(
            """INSERT INTO products (title, description, price, image_url, seller_id, purchase_count, embedding)
               VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (title, description, price, image_url, seller_id, None),
        )

    conn.commit()
    conn.close()
    print("Seed done. You can log in as seller@test.com or buyer@test.com (password: test123).")


if __name__ == "__main__":
    main()
