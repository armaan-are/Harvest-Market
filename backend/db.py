import pathlib
import sqlite3

# Database lives next to this file (backend/market.db)
BASE_DIR = pathlib.Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "market.db"


def _init_schema(conn: sqlite3.Connection) -> None:
    """
    Ensure the SQLite schema exists.

    Migration note:
    Mirrors the schema from backend/database.js (users, products, messages, purchases).
    Uses CREATE TABLE IF NOT EXISTS so it is safe to run repeatedly.
    """
    cur = conn.cursor()

    # Users
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK (role IN ('buyer', 'seller'))
        )
        """
    )

    # Products
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          description TEXT,
          price REAL NOT NULL,
          image_url TEXT,
          seller_id INTEGER NOT NULL,
          purchase_count INTEGER NOT NULL DEFAULT 0,
          embedding TEXT,
          FOREIGN KEY (seller_id) REFERENCES users(id)
        )
        """
    )

    # Messages
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          product_id INTEGER NOT NULL,
          buyer_id INTEGER NOT NULL,
          seller_id INTEGER NOT NULL,
          sender_id INTEGER NOT NULL,
          sender_role TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (product_id) REFERENCES products(id),
          FOREIGN KEY (buyer_id) REFERENCES users(id),
          FOREIGN KEY (seller_id) REFERENCES users(id),
          FOREIGN KEY (sender_id) REFERENCES users(id)
        )
        """
    )

    # Purchases
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS purchases (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          buyer_id INTEGER NOT NULL,
          seller_id INTEGER NOT NULL,
          product_id INTEGER NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (buyer_id) REFERENCES users(id),
          FOREIGN KEY (seller_id) REFERENCES users(id),
          FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """
    )

    conn.commit()


def get_db():
    """
    Dependency that yields a sqlite3 connection.

    Uses row_factory so rows behave like dicts (row["column"]).
    """
    # Allow use across different threads (FastAPI/uvicorn worker threads)
    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    try:
        yield conn
    finally:
        conn.close()

