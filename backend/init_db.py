"""Command-line entry point for initializing the SQLite database."""

from __future__ import annotations

from backend.db import DB_PATH, init_database


def main() -> None:
    """Create the database schema and starter data."""
    init_database()
    print(f"Initialized database at {DB_PATH}")


if __name__ == "__main__":
    main()
