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

        # Book inventory table used by add/view/detail workflows.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                totalCopies INTEGER NOT NULL CHECK (totalCopies >= 1),
                availableCopies INTEGER NOT NULL CHECK (
                    availableCopies >= 0
                    AND availableCopies <= totalCopies
                )
            )
            """
        )

        # Backward compatibility for older books table layouts.
        cursor.execute("PRAGMA table_info(books)")
        book_columns = [row["name"] for row in cursor.fetchall()]
        if "totalCopies" not in book_columns:
            cursor.execute("ALTER TABLE books ADD COLUMN totalCopies INTEGER NOT NULL DEFAULT 1")
        if "availableCopies" not in book_columns:
            cursor.execute(
                "ALTER TABLE books ADD COLUMN availableCopies INTEGER NOT NULL DEFAULT 1"
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


def validate_book_input(title, author, total_copies, available_copies):
    """Validate and normalize book payload before DB insertion."""
    clean_title = (title or "").strip()
    clean_author = (author or "").strip()
    if not clean_title:
        raise ValueError("Book title is required.")
    if not clean_author:
        raise ValueError("Author name is required.")

    try:
        parsed_total = int(total_copies)
    except (TypeError, ValueError):
        raise ValueError("Total copies must be a whole number.")
    if parsed_total < 1:
        raise ValueError("Total copies must be at least 1.")

    try:
        parsed_available = int(available_copies)
    except (TypeError, ValueError):
        raise ValueError("Available copies must be a whole number.")
    if parsed_available < 0:
        raise ValueError("Available copies cannot be negative.")
    if parsed_available > parsed_total:
        raise ValueError("Available copies cannot exceed total copies.")

    return clean_title, clean_author, parsed_total, parsed_available


def create_book(title, author, total_copies, available_copies):
    """Insert a book record using parameterized SQL with explicit commit/close."""
    clean_title, clean_author, parsed_total, parsed_available = validate_book_input(
        title, author, total_copies, available_copies
    )

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO books (title, author, totalCopies, availableCopies)
            VALUES (?, ?, ?, ?)
            """,
            (clean_title, clean_author, parsed_total, parsed_available),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_books():
    """Fetch all books for the view-books page."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, author, totalCopies, availableCopies
            FROM books
            ORDER BY id DESC
            """
        )
        return cursor.fetchall()


def get_book_by_id(book_id):
    """Fetch one book by id."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, author, totalCopies, availableCopies
            FROM books
            WHERE id = ?
            """,
            (book_id,),
        )
        return cursor.fetchone()


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

        # Prefer copy-based totals from required schema.
        total_books = 0
        available_books = 0
        borrowed_books = 0
        try:
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(totalCopies), 0) AS total_books,
                    COALESCE(SUM(availableCopies), 0) AS available_books
                FROM books
                """
            )
            result = cursor.fetchone()
            if result:
                total_books = int(result["total_books"] or 0)
                available_books = int(result["available_books"] or 0)
                borrowed_books = max(total_books - available_books, 0)
        except sqlite3.Error:
            # Legacy fallback if books schema differs.
            total_books = safe_count(cursor, "SELECT COUNT(*) FROM books")
            available_books = safe_count(
                cursor,
                "SELECT COUNT(*) FROM books WHERE LOWER(status) = 'available'",
            )
            borrowed_books = safe_count(
                cursor,
                "SELECT COUNT(*) FROM books WHERE LOWER(status) = 'borrowed'",
            )
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
