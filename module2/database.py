from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "library.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """
        )

        existing_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "password" not in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN password TEXT NOT NULL DEFAULT ''")

        conn.commit()


def search_users_by_name(keyword):
    normalized = (keyword or "").strip()
    if not normalized:
        return []

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, name, email
            FROM users
            WHERE LOWER(name) LIKE LOWER(?)
            ORDER BY name ASC
            """,
            (f"%{normalized}%",),
        ).fetchall()


def delete_user_by_id(user_id):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


init_db()
