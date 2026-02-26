from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import date, timedelta
import sqlite3

from database import init_db, get_connection

app = Flask(__name__)
CORS(app)

init_db()


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({"message": "Library Management System API is running."}), 200


# ── POST /borrow ──────────────────────────────────────────────────────────────
@app.route("/borrow", methods=["POST"])
def borrow_book():
    data = request.get_json()
    user_id = data.get("user_id")
    book_id = data.get("book_id")

    if not user_id or not book_id:
        return jsonify({"error": "user_id and book_id are required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Check user exists
    user = cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found."}), 404

    # Check book exists
    book = cursor.execute("SELECT id, available_copies FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        conn.close()
        return jsonify({"error": "Book not found."}), 404

    # Check available copies
    if book["available_copies"] <= 0:
        conn.close()
        return jsonify({"error": "No available copies for this book."}), 400

    # Check user has not already borrowed this book without returning
    active = cursor.execute("""
        SELECT id FROM transactions
        WHERE user_id = ? AND book_id = ? AND return_date IS NULL
    """, (user_id, book_id)).fetchone()
    if active:
        conn.close()
        return jsonify({"error": "User has already borrowed this book and has not returned it yet."}), 400

    # Insert transaction
    borrow_date = date.today().isoformat()
    due_date = (date.today() + timedelta(days=7)).isoformat()

    cursor.execute("""
        INSERT INTO transactions (user_id, book_id, borrow_date, due_date, return_date)
        VALUES (?, ?, ?, ?, NULL)
    """, (user_id, book_id, borrow_date, due_date))

    # Decrease available copies
    cursor.execute("""
        UPDATE books SET available_copies = available_copies - 1 WHERE id = ?
    """, (book_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Book borrowed successfully.",
        "borrow_date": borrow_date,
        "due_date": due_date
    }), 201


# ── POST /return ──────────────────────────────────────────────────────────────
@app.route("/return", methods=["POST"])
def return_book():
    data = request.get_json()
    user_id = data.get("user_id")
    book_id = data.get("book_id")

    if not user_id or not book_id:
        return jsonify({"error": "user_id and book_id are required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Check active transaction exists
    transaction = cursor.execute("""
        SELECT id FROM transactions
        WHERE user_id = ? AND book_id = ? AND return_date IS NULL
    """, (user_id, book_id)).fetchone()

    if not transaction:
        conn.close()
        return jsonify({"error": "No active borrow record found for this user and book."}), 404

    return_date = date.today().isoformat()

    # Update return date
    cursor.execute("""
        UPDATE transactions SET return_date = ? WHERE id = ?
    """, (return_date, transaction["id"]))

    # Increase available copies
    cursor.execute("""
        UPDATE books SET available_copies = available_copies + 1 WHERE id = ?
    """, (book_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Book returned successfully.",
        "return_date": return_date
    }), 200


# ── GET /transactions/<user_id> ───────────────────────────────────────────────
@app.route("/transactions/<int:user_id>", methods=["GET"])
def get_user_transactions(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Check user exists
    user = cursor.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found."}), 404

    transactions = cursor.execute("""
        SELECT
            t.id,
            t.book_id,
            b.title        AS book_title,
            b.author       AS book_author,
            t.borrow_date,
            t.due_date,
            t.return_date
        FROM transactions t
        JOIN books b ON b.id = t.book_id
        WHERE t.user_id = ?
        ORDER BY t.borrow_date DESC
    """, (user_id,)).fetchall()

    conn.close()

    return jsonify({
        "user_id": user_id,
        "user_name": user["name"],
        "transactions": [dict(row) for row in transactions]
    }), 200

@app.route('/books', methods=['GET'])
def view_books():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, author, available_copies FROM books")
    books = cursor.fetchall()

    conn.close()

    result = []
    for book in books:
        result.append({
            "id": book[0],
            "title": book[1],
            "author": book[2],
            "available_copies": book[3]
        })

    return jsonify(result)

@app.route('/transactions/active/<int:user_id>', methods=['GET'])
def active_borrowed_books(user_id):
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.id, b.title, t.borrow_date, t.due_date
        FROM transactions t
        INNER JOIN books b ON t.book_id = b.id
        WHERE t.user_id = ? AND t.return_date IS NULL
    """, (user_id,))

    records = cursor.fetchall()
    conn.close()

    result = []
    for row in records:
        result.append({
            "transaction_id": row[0],
            "book_title": row[1],
            "borrow_date": row[2],
            "due_date": row[3]
        })

    return jsonify(result)


@app.route('/books/<int:book_id>/availability', methods=['GET'])
def check_availability(book_id):
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    cursor.execute("SELECT available_copies FROM books WHERE id=?", (book_id,))
    book = cursor.fetchone()

    conn.close()

    if not book:
        return jsonify({"error": "Book not found"}), 404

    available = book[0]

    return jsonify({
        "book_id": book_id,
        "available_copies": available,
        "available": available > 0
    })
    
    
# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(port=5000, debug=True)
    
