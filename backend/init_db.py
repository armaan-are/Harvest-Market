"""Command-line entry point for initializing the SQLite database."""

from __future__ import annotations

import os

from backend.database import DEFAULT_DB_PATH, initialize_database


def main() -> None:
    """Create the database schema and starter data."""
    database_path = os.environ.get("TEAM21_DB_PATH", str(DEFAULT_DB_PATH))
    path = initialize_database(database_path)
    print(f"Initialized database at {path}")


if __name__ == "__main__":
    main()
