from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import date, timedelta
from database import (
    init_db,
    get_connection,
    has_active_borrow,
    create_borrow_transaction,
    return_book_transaction,
    get_current_borrows,
    get_borrow_history,
)

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"
CORS(
    app,
    supports_credentials=True,
    origins=["http://127.0.0.1:5501", "http://localhost:5501"],
)

init_db()


@app.route("/")
def index():
    return jsonify({"message": "Library Management System API running"}), 200


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "user_id" not in data:
        return jsonify({"error": "User ID required"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    session["user_id"] = user_id
    return jsonify({"message": "Login successful"}), 200


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@app.route("/borrow", methods=["POST"])
def borrow_book():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    if not data or "book_id" not in data:
        return jsonify({"error": "Book ID required"}), 400

    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        book = cursor.execute(
            "SELECT id, available_copies FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()
    finally:
        conn.close()

    if not book:
        return jsonify({"error": "Book not found"}), 404

    if book["available_copies"] <= 0:
        return jsonify({"error": "No available copies"}), 400

    if has_active_borrow(user_id, book_id):
        return jsonify({"error": "You already borrowed this book"}), 400

    create_borrow_transaction(user_id, book_id)

    return jsonify(
        {
            "message": "Book borrowed successfully",
            "borrow_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        }
    ), 201


@app.route("/return", methods=["POST"])
def return_book():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    if not data or "book_id" not in data:
        return jsonify({"error": "Book ID required"}), 400

    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400

    if not has_active_borrow(user_id, book_id):
        return jsonify({"error": "No active borrow record found"}), 404

    return_book_transaction(user_id, book_id)

    return jsonify(
        {
            "message": "Book returned successfully",
            "return_date": date.today().isoformat(),
        }
    ), 200

@app.route("/my-transactions", methods=["GET"])
def my_transactions():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    history = get_borrow_history(user_id)
    return jsonify([dict(row) for row in history]), 200



@app.route("/books", methods=["GET"])
def view_books():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        books = cursor.execute(
            "SELECT id, title, author, available_copies FROM books"
        ).fetchall()
    finally:
        conn.close()

    return jsonify([dict(row) for row in books]), 200


@app.route("/books/<int:book_id>/availability", methods=["GET"])
def check_availability(book_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        book = cursor.execute(
            "SELECT available_copies FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()
    finally:
        conn.close()

    if not book:
        return jsonify({"error": "Book not found"}), 404

    return jsonify(
        {
            "book_id": book_id,
            "available_copies": book["available_copies"],
            "available": book["available_copies"] > 0,
        }
    ), 200


if __name__ == "__main__":
    app.run(debug=True)
