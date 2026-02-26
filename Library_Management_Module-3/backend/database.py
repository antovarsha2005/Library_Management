import sqlite3
from datetime import datetime, timedelta

DATABASE = "library.db"


def get_connection():
    conn = sqlite3.connect(
        DATABASE,
        timeout=10,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                available_copies INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                borrow_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (book_id) REFERENCES books(id)
            )
            """
        )

        conn.commit()
    finally:
        conn.close()


def has_active_borrow(user_id, book_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        transaction = cursor.execute(
            """
            SELECT id FROM transactions
            WHERE user_id = ? AND book_id = ?
            AND return_date IS NULL
            """,
            (user_id, book_id),
        ).fetchone()
        conn.commit()
        return transaction is not None
    finally:
        conn.close()


def create_borrow_transaction(user_id, book_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        borrow_date = datetime.now()
        due_date = borrow_date + timedelta(days=7)

        cursor.execute(
            """
            INSERT INTO transactions (user_id, book_id, borrow_date, due_date)
            VALUES (?, ?, ?, ?)
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
            SET available_copies = available_copies - 1
            WHERE id = ?
            """,
            (book_id,),
        )

        conn.commit()
    finally:
        conn.close()


def return_book_transaction(user_id, book_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        return_date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            """
            UPDATE transactions
            SET return_date = ?
            WHERE user_id = ? AND book_id = ?
            AND return_date IS NULL
            """,
            (return_date, user_id, book_id),
        )

        cursor.execute(
            """
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE id = ?
            """,
            (book_id,),
        )

        conn.commit()
    finally:
        conn.close()


def get_current_borrows(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        rows = cursor.execute(
            """
            SELECT b.id AS book_id,
                   b.title,
                   t.borrow_date,
                   t.due_date
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            WHERE t.user_id = ?
            AND t.return_date IS NULL
            """,
            (user_id,),
        ).fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def get_borrow_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        rows = cursor.execute(
            """
            SELECT b.title,
                   t.borrow_date,
                   t.due_date,
                   t.return_date
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            WHERE t.user_id = ?
            ORDER BY t.borrow_date DESC
            """,
            (user_id,),
        ).fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()