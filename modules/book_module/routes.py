from functools import wraps
import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    build_dashboard_stats,
    create_book,
    delete_book_by_id,
    display_role,
    email_exists,
    get_all_books,
    get_book_by_id,
    get_user_by_id,
    normalize_role,
    search_books_by_title_or_author,
    update_book as update_book_record,
    update_user_profile,
)


book_bp = Blueprint("book", __name__)


def role_badge_class(role):
    safe_role = normalize_role(role)
    return f"badge-{safe_role}"


def set_user_session(user):
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["role"] = normalize_role(user["role"])


def _password_matches(stored_password, plain_password):
    if not stored_password:
        return False
    try:
        if check_password_hash(stored_password, plain_password):
            return True
    except ValueError:
        pass
    return stored_password == plain_password


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        user = get_user_by_id(user_id)
        if not user:
            session.clear()
            flash("Session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        set_user_session(user)
        return route_function(*args, **kwargs)

    return wrapper


def librarian_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if session.get("role") != "librarian":
            flash("Access denied.", "error")
            return redirect(url_for("role_dashboard"))
        return route_function(*args, **kwargs)

    return wrapper


@book_bp.route("/")
@login_required
@librarian_required
def home():
    return redirect(url_for("book.dashboard"))


@book_bp.route("/dashboard")
@login_required
@librarian_required
def dashboard():
    stats = build_dashboard_stats()
    return render_template(
        "librarian/dashboard.html",
        name=session.get("user_name", "Member"),
        email=session.get("user_email", ""),
        role=display_role(session.get("role", "user")),
        role_badge=role_badge_class(session.get("role", "user")),
        stats=stats,
        nav_active="dashboard",
    )


@book_bp.route("/manage-books")
@login_required
@librarian_required
def manage_books():
    return render_template("librarian/manage_books.html", nav_active="manage_books")


@book_bp.route("/add-book", methods=["GET", "POST"])
@login_required
@librarian_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "")
        author = request.form.get("author", "")
        total_copies = request.form.get("totalCopies", "")
        available_copies = request.form.get("availableCopies", "")

        try:
            create_book(title, author, total_copies, available_copies)
            flash("Book added successfully.", "success")
            return redirect(url_for("book.manage_books"))
        except ValueError as validation_error:
            flash(str(validation_error), "error")
            return redirect(url_for("book.add_book"))
        except sqlite3.Error:
            flash("Could not save the book right now. Please try again.", "error")
            return redirect(url_for("book.add_book"))

    return render_template("librarian/add_book.html", nav_active="manage_books")


@book_bp.route("/view-books")
@login_required
@librarian_required
def view_books():
    search_query = request.args.get("search", "").strip()
    try:
        if search_query:
            books = search_books_by_title_or_author(search_query)
        else:
            books = get_all_books()
    except sqlite3.Error:
        flash("Could not load books right now. Please try again.", "error")
        books = []

    return render_template(
        "librarian/view_books.html",
        books=books,
        search_query=search_query,
        nav_active="manage_books",
    )


@book_bp.route("/book/<int:id>")
@login_required
@librarian_required
def book_detail(id):
    try:
        book = get_book_by_id(id)
    except sqlite3.Error:
        flash("Could not load book details right now. Please try again.", "error")
        return redirect(url_for("book.view_books"))

    if not book:
        flash("Book not found.", "error")
        return redirect(url_for("book.view_books"))

    return render_template(
        "librarian/book_detail.html",
        book=book,
        nav_active="manage_books",
    )


@book_bp.route("/edit-book/<int:id>", methods=["GET", "POST"])
@login_required
@librarian_required
def edit_book(id):
    try:
        book = get_book_by_id(id)
    except sqlite3.Error:
        flash("Could not load book details right now. Please try again.", "error")
        return redirect(url_for("book.view_books"))

    if not book:
        flash("Book not found.", "error")
        return redirect(url_for("book.view_books"))

    if request.method == "POST":
        title = request.form.get("title", "")
        author = request.form.get("author", "")
        total_copies = request.form.get("totalCopies", "")
        available_copies = request.form.get("availableCopies", "")

        try:
            updated = update_book_record(id, title, author, total_copies, available_copies)
            if not updated:
                flash("Book not found.", "error")
                return redirect(url_for("book.view_books"))

            flash("Book updated successfully.", "success")
            return redirect(url_for("book.book_detail", id=id))
        except ValueError as validation_error:
            flash(str(validation_error), "error")
            book = {
                "id": id,
                "title": (title or "").strip(),
                "author": (author or "").strip(),
                "totalCopies": total_copies,
                "availableCopies": available_copies,
            }
            return render_template(
                "librarian/edit_book.html",
                book=book,
                nav_active="manage_books",
            )
        except sqlite3.Error:
            flash("Could not update the book right now. Please try again.", "error")
            return redirect(url_for("book.edit_book", id=id))

    return render_template("librarian/edit_book.html", book=book, nav_active="manage_books")


@book_bp.route("/update-book")
@login_required
@librarian_required
def update_book():
    return render_template("librarian/update_book.html", nav_active="manage_books")


@book_bp.route("/search-books")
@login_required
@librarian_required
def search_books():
    return render_template("librarian/search_books.html", nav_active="manage_books")


@book_bp.route("/delete-book")
@login_required
@librarian_required
def delete_book_legacy():
    return redirect(url_for("book.view_books"))


@book_bp.route("/delete-book/<int:id>", methods=["POST"])
@login_required
@librarian_required
def delete_book(id):
    try:
        deleted = delete_book_by_id(id)
        if not deleted:
            flash("Book not found.", "error")
            return redirect(url_for("book.view_books"))

        flash("Book deleted successfully.", "success")
        return redirect(url_for("book.view_books"))
    except sqlite3.Error:
        flash("Could not delete the book right now. Please try again.", "error")
        return redirect(url_for("book.view_books"))


@book_bp.route("/profile", methods=["GET", "POST"])
@login_required
@librarian_required
def profile():
    user = get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email:
            flash("Name and email cannot be empty.", "error")
            return redirect(url_for("book.profile"))

        try:
            if email_exists(email, exclude_user_id=user["id"]):
                flash("This email is already in use by another account.", "error")
                return redirect(url_for("book.profile"))

            hashed_password = None
            wants_password_change = any([current_password, new_password, confirm_password])
            if wants_password_change:
                if not current_password:
                    flash("Enter your current password to set a new password.", "error")
                    return redirect(url_for("book.profile"))
                if not _password_matches(user["password"], current_password):
                    flash("Current password is incorrect.", "error")
                    return redirect(url_for("book.profile"))
                if not new_password:
                    flash("New password cannot be empty.", "error")
                    return redirect(url_for("book.profile"))
                if new_password != confirm_password:
                    flash("New password and confirm password do not match.", "error")
                    return redirect(url_for("book.profile"))
                hashed_password = generate_password_hash(new_password)

            update_user_profile(user["id"], name, email, hashed_password=hashed_password)
            refreshed_user = get_user_by_id(user["id"])
            if refreshed_user:
                set_user_session(refreshed_user)
            flash("Profile updated successfully.", "success")
            return redirect(url_for("book.profile"))
        except sqlite3.Error:
            flash("Could not update your profile right now. Please try again.", "error")
            return redirect(url_for("book.profile"))

    return render_template(
        "librarian/profile.html",
        name=user["name"],
        email=user["email"],
        role=display_role(user["role"]),
        role_badge=role_badge_class(user["role"]),
        nav_active="profile",
    )
