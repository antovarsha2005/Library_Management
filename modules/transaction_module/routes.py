from datetime import date, timedelta
from functools import wraps

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from database import (
    create_borrow_transaction,
    get_books_for_user_dashboard,
    get_borrow_history,
    get_connection,
    get_current_borrows,
    get_user_by_id,
    has_active_borrow,
    normalize_role,
    return_book_transaction,
)


transaction_bp = Blueprint("transaction", __name__)


def set_user_session(user):
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["role"] = normalize_role(user["role"])


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login"))

        user = get_user_by_id(user_id)
        if not user:
            session.clear()
            return redirect(url_for("login"))

        set_user_session(user)
        return route_function(*args, **kwargs)

    return wrapper


def user_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if session.get("role") != "user":
            return redirect(url_for("role_dashboard"))
        return route_function(*args, **kwargs)

    return wrapper


def api_user_auth():
    user_id = session.get("user_id")
    if not user_id:
        return None, (jsonify({"error": "Not logged in"}), 401)

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return None, (jsonify({"error": "Not logged in"}), 401)

    set_user_session(user)
    if normalize_role(user["role"]) != "user":
        return None, (jsonify({"error": "Forbidden"}), 403)

    return user, None


@transaction_bp.route("/")
@login_required
@user_required
def home():
    return redirect(url_for("transaction.dashboard"))


@transaction_bp.route("/dashboard")
@login_required
@user_required
def dashboard():
    return render_template(
        "user/dashboard.html",
        user_id=session.get("user_id"),
        default_panel="overview",
    )


@transaction_bp.route("/transactions")
@login_required
@user_required
def transactions_page():
    return render_template(
        "user/transactions.html",
        user_id=session.get("user_id"),
        default_panel="history",
    )


@transaction_bp.route("/borrow", methods=["POST"])
def borrow_book():
    user, auth_error = api_user_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    if "book_id" not in data:
        return jsonify({"error": "Book ID required"}), 400

    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400

    conn = get_connection()
    try:
        cursor = conn.cursor()
        book = cursor.execute(
            "SELECT id, availableCopies FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()
    finally:
        conn.close()

    if not book:
        return jsonify({"error": "Book not found"}), 404

    if book["availableCopies"] <= 0:
        return jsonify({"error": "No available copies"}), 400

    if has_active_borrow(user["id"], book_id):
        return jsonify({"error": "You already borrowed this book"}), 400

    create_borrow_transaction(user["id"], book_id)

    return (
        jsonify(
            {
                "message": "Book borrowed successfully",
                "borrow_date": date.today().isoformat(),
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
            }
        ),
        201,
    )


@transaction_bp.route("/return", methods=["POST"])
def return_book():
    user, auth_error = api_user_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    if "book_id" not in data:
        return jsonify({"error": "Book ID required"}), 400

    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400

    if not has_active_borrow(user["id"], book_id):
        return jsonify({"error": "No active borrow record found"}), 404

    return_book_transaction(user["id"], book_id)

    return (
        jsonify(
            {
                "message": "Book returned successfully",
                "return_date": date.today().isoformat(),
            }
        ),
        200,
    )


@transaction_bp.route("/login", methods=["POST"])
def legacy_login():
    """Legacy module-3 API login retained for backward compatibility."""
    data = request.get_json(silent=True) or {}

    if "user_id" not in data:
        return jsonify({"error": "User ID required"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    set_user_session(user)
    return jsonify({"message": "Login successful"}), 200


@transaction_bp.route("/logout", methods=["POST"])
def legacy_logout():
    """Legacy module-3 API logout retained for backward compatibility."""
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@transaction_bp.route("/my-transactions", methods=["GET"])
def my_transactions():
    user, auth_error = api_user_auth()
    if auth_error:
        return auth_error

    history = get_borrow_history(user["id"])
    return jsonify([dict(row) for row in history]), 200


@transaction_bp.route("/my-active-books", methods=["GET"])
def my_active_books():
    user, auth_error = api_user_auth()
    if auth_error:
        return auth_error

    active = get_current_borrows(user["id"])
    return jsonify([dict(row) for row in active]), 200


@transaction_bp.route("/books", methods=["GET"])
def view_books():
    user, auth_error = api_user_auth()
    if auth_error:
        return auth_error

    books = get_books_for_user_dashboard()
    payload = [
        {
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "available_copies": row["availableCopies"],
        }
        for row in books
    ]
    return jsonify(payload), 200


@transaction_bp.route("/books/<int:book_id>/availability", methods=["GET"])
def check_availability(book_id):
    user, auth_error = api_user_auth()
    if auth_error:
        return auth_error

    conn = get_connection()
    try:
        cursor = conn.cursor()
        book = cursor.execute(
            "SELECT availableCopies FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()
    finally:
        conn.close()

    if not book:
        return jsonify({"error": "Book not found"}), 404

    return (
        jsonify(
            {
                "book_id": book_id,
                "available_copies": book["availableCopies"],
                "available": book["availableCopies"] > 0,
            }
        ),
        200,
    )
