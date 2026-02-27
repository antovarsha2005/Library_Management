from datetime import datetime, timedelta
import sqlite3

from config import DATABASE_PATH

DATABASE = DATABASE_PATH

ROLE_VALUES = ("admin", "librarian", "user")
SIGNUP_ROLES = ("Admin", "Librarian", "User")
ROLE_LABELS = {
    "admin": "Admin",
    "librarian": "Librarian",
    "user": "User",
}


def get_db():
    """Return a SQLite connection configured for dict-style row access."""
    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_connection():
    """Backward-compatible alias used by legacy module code."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def normalize_role(role_value):
    """Normalize role values across legacy and unified schema variants."""
    role = (role_value or "").strip()
    if not role:
        return "user"

    lowered = role.lower()
    if lowered in ROLE_VALUES:
        return lowered

    uppered = role.upper()
    if uppered in {"ADMIN", "LIBRARIAN", "USER"}:
        return uppered.lower()

    return "user"


def display_role(role_value):
    """Return title-cased role text for UI rendering."""
    return ROLE_LABELS.get(normalize_role(role_value), "User")


def _column_names(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row["name"] for row in cursor.fetchall()]


def _align_users_schema(cursor):
    columns = _column_names(cursor, "users")

    if "password" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT NOT NULL DEFAULT ''")
    if "role" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    if "created_at" not in columns:
        try:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")

    cursor.execute(
        """
        UPDATE users
        SET role = CASE UPPER(TRIM(COALESCE(role, '')))
            WHEN 'ADMIN' THEN 'admin'
            WHEN 'LIBRARIAN' THEN 'librarian'
            WHEN 'USER' THEN 'user'
            ELSE 'user'
        END
        """
    )
    cursor.execute(
        """
        UPDATE users
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL OR TRIM(CAST(created_at AS TEXT)) = ''
        """
    )


def _align_books_schema(cursor):
    columns = _column_names(cursor, "books")

    if "totalCopies" not in columns:
        cursor.execute("ALTER TABLE books ADD COLUMN totalCopies INTEGER NOT NULL DEFAULT 1")
    if "availableCopies" not in columns:
        if "available_copies" in columns:
            cursor.execute(
                "ALTER TABLE books ADD COLUMN availableCopies INTEGER NOT NULL DEFAULT 1"
            )
            cursor.execute(
                "UPDATE books SET availableCopies = COALESCE(available_copies, 1)"
            )
        else:
            cursor.execute(
                "ALTER TABLE books ADD COLUMN availableCopies INTEGER NOT NULL DEFAULT 1"
            )

    cursor.execute(
        "UPDATE books SET totalCopies = 1 WHERE totalCopies IS NULL OR totalCopies < 1"
    )
    cursor.execute(
        "UPDATE books SET availableCopies = totalCopies WHERE availableCopies IS NULL"
    )
    cursor.execute("UPDATE books SET availableCopies = 0 WHERE availableCopies < 0")
    cursor.execute(
        """
        UPDATE books
        SET availableCopies = totalCopies
        WHERE availableCopies > totalCopies
        """
    )


def _align_transactions_schema(cursor):
    columns = _column_names(cursor, "transactions")

    if "user_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")
    if "book_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN book_id INTEGER")
    if "borrow_date" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN borrow_date TEXT")
    if "return_date" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN return_date TEXT")
    if "status" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN status TEXT")
    if "due_date" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN due_date TEXT")

    cursor.execute(
        """
        UPDATE transactions
        SET status = CASE
            WHEN return_date IS NULL OR TRIM(return_date) = '' THEN 'borrowed'
            ELSE 'returned'
        END
        WHERE status IS NULL OR TRIM(status) = ''
        """
    )


def init_db():
    """Create and align unified tables used by all modules."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','librarian','user')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                totalCopies INTEGER NOT NULL,
                availableCopies INTEGER NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book_id INTEGER,
                borrow_date TEXT,
                return_date TEXT,
                status TEXT,
                due_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(book_id) REFERENCES books(id)
            )
            """
        )

        _align_users_schema(cursor)
        _align_books_schema(cursor)
        _align_transactions_schema(cursor)

        conn.commit()


def get_user_by_id(user_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, name, email, password, role, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()


def get_user_by_email(email):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, name, email, password, role, created_at
            FROM users
            WHERE email = ?
            """,
            ((email or "").strip().lower(),),
        ).fetchone()


def email_exists(email, exclude_user_id=None):
    with get_db() as conn:
        if exclude_user_id is None:
            row = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                ((email or "").strip().lower(),),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?",
                ((email or "").strip().lower(), exclude_user_id),
            ).fetchone()
        return row is not None


def create_user(name, email, password, role):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                (name or "").strip(),
                (email or "").strip().lower(),
                password,
                normalize_role(role),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_user_profile(user_id, name, email, hashed_password=None):
    with get_db() as conn:
        cursor = conn.cursor()
        if hashed_password is None:
            cursor.execute(
                "UPDATE users SET name = ?, email = ? WHERE id = ?",
                ((name or "").strip(), (email or "").strip().lower(), user_id),
            )
        else:
            cursor.execute(
                """
                UPDATE users
                SET name = ?, email = ?, password = ?
                WHERE id = ?
                """,
                (
                    (name or "").strip(),
                    (email or "").strip().lower(),
                    hashed_password,
                    user_id,
                ),
            )
        conn.commit()


def get_all_users():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, name, email, password, role, created_at
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()


def search_users_by_name(keyword):
    normalized = (keyword or "").strip()
    if not normalized:
        return []

    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, name, email, role
            FROM users
            WHERE LOWER(name) LIKE LOWER(?)
            ORDER BY name ASC
            """,
            (f"%{normalized}%",),
        ).fetchall()


def update_user_record(user_id, name, email, password, role=None):
    with get_db() as conn:
        cursor = conn.cursor()
        if role is None:
            cursor.execute(
                """
                UPDATE users
                SET name = ?, email = ?, password = ?
                WHERE id = ?
                """,
                (
                    (name or "").strip(),
                    (email or "").strip().lower(),
                    (password or "").strip(),
                    user_id,
                ),
            )
        else:
            cursor.execute(
                """
                UPDATE users
                SET name = ?, email = ?, password = ?, role = ?
                WHERE id = ?
                """,
                (
                    (name or "").strip(),
                    (email or "").strip().lower(),
                    (password or "").strip(),
                    normalize_role(role),
                    user_id,
                ),
            )
        conn.commit()
        return cursor.rowcount > 0


def delete_user_by_id(user_id):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def validate_book_input(title, author, total_copies, available_copies):
    clean_title = (title or "").strip()
    clean_author = (author or "").strip()
    if not clean_title:
        raise ValueError("Book title is required.")
    if not clean_author:
        raise ValueError("Author name is required.")

    try:
        parsed_total = int(total_copies)
    except (TypeError, ValueError) as exc:
        raise ValueError("Total copies must be a whole number.") from exc
    if parsed_total < 1:
        raise ValueError("Total copies must be at least 1.")

    try:
        parsed_available = int(available_copies)
    except (TypeError, ValueError) as exc:
        raise ValueError("Available copies must be a whole number.") from exc
    if parsed_available < 0:
        raise ValueError("Available copies cannot be negative.")
    if parsed_available > parsed_total:
        raise ValueError("Available copies cannot exceed total copies.")

    return clean_title, clean_author, parsed_total, parsed_available


def create_book(title, author, total_copies, available_copies):
    clean_title, clean_author, parsed_total, parsed_available = validate_book_input(
        title, author, total_copies, available_copies
    )

    with get_db() as conn:
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


def update_book(book_id, title, author, total_copies, available_copies):
    clean_title, clean_author, parsed_total, parsed_available = validate_book_input(
        title, author, total_copies, available_copies
    )

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE books
            SET title = ?, author = ?, totalCopies = ?, availableCopies = ?
            WHERE id = ?
            """,
            (clean_title, clean_author, parsed_total, parsed_available, book_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_book_by_id(book_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_all_books():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, title, author, totalCopies, availableCopies
            FROM books
            ORDER BY id DESC
            """
        ).fetchall()


def search_books_by_title_or_author(search_query):
    query_text = (search_query or "").strip()
    if not query_text:
        return get_all_books()

    like_pattern = f"%{query_text}%"
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, title, author, totalCopies, availableCopies
            FROM books
            WHERE title LIKE ? COLLATE NOCASE
               OR author LIKE ? COLLATE NOCASE
            ORDER BY id DESC
            """,
            (like_pattern, like_pattern),
        ).fetchall()


def get_book_by_id(book_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, title, author, totalCopies, availableCopies
            FROM books
            WHERE id = ?
            """,
            (book_id,),
        ).fetchone()


def get_books_for_user_dashboard():
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, title, author, totalCopies, availableCopies
            FROM books
            ORDER BY id ASC
            """
        ).fetchall()


def has_active_borrow(user_id, book_id):
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM transactions
            WHERE user_id = ?
              AND book_id = ?
              AND (return_date IS NULL OR return_date = '')
            """,
            (user_id, book_id),
        ).fetchone()
        return row is not None


def create_borrow_transaction(user_id, book_id):
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=7)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (user_id, book_id, borrow_date, return_date, status, due_date)
            VALUES (?, ?, ?, NULL, 'borrowed', ?)
            """,
            (
                user_id,
                book_id,
                borrow_date.strftime("%Y-%m-%d"),
                due_date.strftime("%Y-%m-%d"),
            ),
        )

        cursor.execute(
            """
            UPDATE books
            SET availableCopies = availableCopies - 1
            WHERE id = ?
            """,
            (book_id,),
        )

        conn.commit()


def return_book_transaction(user_id, book_id):
    return_date = datetime.now().strftime("%Y-%m-%d")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE transactions
            SET return_date = ?, status = 'returned'
            WHERE id = (
                SELECT id
                FROM transactions
                WHERE user_id = ?
                  AND book_id = ?
                  AND (return_date IS NULL OR return_date = '')
                ORDER BY id DESC
                LIMIT 1
            )
            """,
            (return_date, user_id, book_id),
        )
        updated = cursor.rowcount > 0

        if updated:
            cursor.execute(
                """
                UPDATE books
                SET availableCopies = availableCopies + 1
                WHERE id = ?
                """,
                (book_id,),
            )

        conn.commit()
        return updated


def get_current_borrows(user_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT b.id AS book_id,
                   b.title,
                   b.author,
                   t.borrow_date,
                   t.due_date
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            WHERE t.user_id = ?
              AND (t.return_date IS NULL OR t.return_date = '')
            ORDER BY t.borrow_date DESC
            """,
            (user_id,),
        ).fetchall()


def get_borrow_history(user_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT t.id,
                   t.user_id,
                   t.book_id,
                   b.title AS book_title,
                   t.borrow_date,
                   t.due_date,
                   t.return_date,
                   t.status
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            WHERE t.user_id = ?
            ORDER BY t.id DESC
            """,
            (user_id,),
        ).fetchall()


def safe_count(cursor, query, params=()):
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0


def build_dashboard_stats():
    with get_db() as conn:
        cursor = conn.cursor()

        total_users = safe_count(cursor, "SELECT COUNT(*) FROM users")

        total_titles = 0
        total_books = 0
        available_books = 0
        borrowed_books = 0
        try:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_titles,
                    COALESCE(SUM(totalCopies), 0) AS total_books,
                    COALESCE(SUM(availableCopies), 0) AS available_books
                FROM books
                """
            )
            result = cursor.fetchone()
            if result:
                total_titles = int(result["total_titles"] or 0)
                total_books = int(result["total_books"] or 0)
                available_books = int(result["available_books"] or 0)
                borrowed_books = max(total_books - available_books, 0)
        except sqlite3.Error:
            total_titles = safe_count(cursor, "SELECT COUNT(*) FROM books")
            total_books = total_titles
            available_books = total_titles
            borrowed_books = 0

        active_members = safe_count(
            cursor,
            """
            SELECT COUNT(DISTINCT user_id)
            FROM transactions
            WHERE DATE(borrow_date) >= DATE('now', '-30 day')
            """,
        )
        if active_members == 0:
            active_members = total_users

    return {
        "total_titles": total_titles,
        "total_books": total_books,
        "available_books": available_books,
        "borrowed_books": borrowed_books,
        "total_users": total_users,
        "active_members": active_members,
        "overdue_books": 0,
    }


def build_admin_dashboard_stats():
    with get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        books_row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_titles,
                COALESCE(SUM(totalCopies), 0) AS total_books
            FROM books
            """
        ).fetchone()

        total_books = int(books_row["total_books"] or 0) if books_row else 0
        if total_books == 0 and books_row:
            total_books = int(books_row["total_titles"] or 0)

        active_members = conn.execute(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM transactions
            WHERE DATE(borrow_date) >= DATE('now', '-30 day')
            """
        ).fetchone()[0]
        if not active_members:
            active_members = total_users

    return {
        "total_users": total_users,
        "total_books": total_books,
        "active_members": active_members,
    }
