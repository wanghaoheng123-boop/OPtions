import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"
DB_PATH = BASE_DIR / "episodes.db"


def initialize_database() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.executescript(schema)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Initialized episodic state database.")
