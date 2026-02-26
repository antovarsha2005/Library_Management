from pathlib import Path
import sqlite3

DATABASE = Path(__file__).parent / "library.db"
ROLES = ("Librarian", "Admin", "User")
ROLE_MAP = {"LIBRARIAN": "Librarian", "ADMIN": "Admin", "USER": "User"}


def get_db():
    """Return a SQLite connection configured for dict-style row access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_role(role_value):
    """Normalize stored role text so older uppercase records stay usable."""
    role = (role_value or "").strip()
    if role in ROLES:
        return role
    return ROLE_MAP.get(role.upper(), "User")


def init_db():
    """Create and minimally align the users table schema if needed."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )

        # Backward compatibility: add missing role column for older DB files.
        cursor.execute("PRAGMA table_info(users)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "role" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'User'")

        # Normalize legacy uppercase role values once at startup.
        cursor.execute(
            """
            UPDATE users
            SET role = CASE UPPER(role)
                WHEN 'LIBRARIAN' THEN 'Librarian'
                WHEN 'ADMIN' THEN 'Admin'
                WHEN 'USER' THEN 'User'
                ELSE role
            END
            """
        )
        conn.commit()


def get_user_by_id(user_id):
    """Fetch a single user by id."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email, password, role FROM users WHERE id = ?",
            (user_id,),
        )
        return cursor.fetchone()


def get_user_by_email(email):
    """Fetch a single user by email."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email, password, role FROM users WHERE email = ?",
            (email,),
        )
        return cursor.fetchone()


def email_exists(email, exclude_user_id=None):
    """Check whether an email is already registered."""
    with get_db() as conn:
        cursor = conn.cursor()
        if exclude_user_id is None:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        else:
            cursor.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?",
                (email, exclude_user_id),
            )
        return cursor.fetchone() is not None


def create_user(name, email, hashed_password, role):
    """Create a user account."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, role),
        )
        conn.commit()


def update_user_profile(user_id, name, email, hashed_password=None):
    """Update user profile, optionally including password."""
    with get_db() as conn:
        cursor = conn.cursor()
        if hashed_password is None:
            cursor.execute(
                "UPDATE users SET name = ?, email = ? WHERE id = ?",
                (name, email, user_id),
            )
        else:
            cursor.execute(
                "UPDATE users SET name = ?, email = ?, password = ? WHERE id = ?",
                (name, email, hashed_password, user_id),
            )
        conn.commit()


def safe_count(cursor, query, params=()):
    """Execute count query safely and return 0 when optional tables do not exist."""
    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return int(result[0]) if result else 0
    except sqlite3.Error:
        return 0


def build_dashboard_stats():
    """Collect dashboard metrics with safe fallbacks when book tables are absent."""
    with get_db() as conn:
        cursor = conn.cursor()

        total_users = safe_count(cursor, "SELECT COUNT(*) FROM users")
        total_books = safe_count(cursor, "SELECT COUNT(*) FROM books")

        # Prefer status-based counts when that column/table exists.
        available_books = safe_count(
            cursor,
            "SELECT COUNT(*) FROM books WHERE LOWER(status) = 'available'",
        )
        borrowed_books = safe_count(
            cursor,
            "SELECT COUNT(*) FROM books WHERE LOWER(status) = 'borrowed'",
        )

        # Fallback if there is no status column but books table exists.
        if total_books and available_books == 0 and borrowed_books == 0:
            available_books = total_books

        overdue_books = safe_count(
            cursor,
            """
            SELECT COUNT(*)
            FROM borrow_records
            WHERE DATE(due_date) < DATE('now')
              AND (returned_on IS NULL OR returned_on = '')
            """,
        )

        active_members = safe_count(
            cursor,
            """
            SELECT COUNT(DISTINCT user_id)
            FROM borrow_records
            WHERE DATE(borrowed_on) >= DATE('now', '-30 day')
            """,
        )
        if active_members == 0:
            active_members = total_users

    return {
        "total_books": total_books,
        "available_books": available_books,
        "borrowed_books": borrowed_books,
        "total_users": total_users,
        "active_members": active_members,
        "overdue_books": overdue_books,
    }
