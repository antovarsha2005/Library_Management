from functools import wraps
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    ROLES,
    build_dashboard_stats,
    create_book,
    create_user,
    email_exists,
    get_all_books,
    get_book_by_id,
    get_user_by_email,
    get_user_by_id,
    init_db,
    normalize_role,
    update_user_profile,
)

app = Flask(__name__)
# SECURITY: replace with an environment value in production.
app.secret_key = "change-this-secret-key-in-production"


def role_badge_class(role):
    """Map role to a CSS class used by profile/dashboard role badges."""
    safe_role = normalize_role(role).lower()
    return f"badge-{safe_role}"


def set_user_session(user):
    """Persist user identity in session after login/profile update."""
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["role"] = normalize_role(user["role"])


def login_required(route_function):
    """Protect routes that require an authenticated user session."""

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


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "").strip()

        if not all([name, email, password, confirm_password, role]):
            flash("Name, email, password, confirm password, and role are required.", "error")
            return redirect(url_for("signup"))

        if role not in ROLES:
            flash("Please select a valid role.", "error")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Password and confirm password do not match.", "error")
            return redirect(url_for("signup"))

        try:
            if email_exists(email):
                flash("This email is already registered. Please use a different one.", "error")
                return redirect(url_for("signup"))

            hashed_password = generate_password_hash(password)
            create_user(name, email, hashed_password, role)

            flash("Signup successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("This email is already registered. Please use a different one.", "error")
            return redirect(url_for("signup"))
        except sqlite3.Error:
            flash("Unable to create your account right now. Please try again.", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html", roles=ROLES)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("login"))

        try:
            user = get_user_by_email(email)
            if not user or not check_password_hash(user["password"], password):
                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))

            set_user_session(user)
            flash("Welcome back.", "success")
            return redirect(url_for("dashboard"))
        except sqlite3.Error:
            flash("Unable to log in right now. Please try again.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    stats = build_dashboard_stats()
    return render_template(
        "dashboard.html",
        name=session.get("user_name", "Member"),
        email=session.get("user_email", ""),
        role=session.get("role", "User"),
        role_badge=role_badge_class(session.get("role", "User")),
        stats=stats,
        nav_active="dashboard",
    )


@app.route("/manage-books")
@login_required
def manage_books():
    return render_template("manage_books.html", nav_active="manage_books")


@app.route("/add-book", methods=["GET", "POST"])
@login_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "")
        author = request.form.get("author", "")
        total_copies = request.form.get("totalCopies", "")
        available_copies = request.form.get("availableCopies", "")

        try:
            create_book(title, author, total_copies, available_copies)
            flash("Book added successfully.", "success")
            return redirect(url_for("manage_books"))
        except ValueError as validation_error:
            flash(str(validation_error), "error")
            return redirect(url_for("add_book"))
        except sqlite3.Error:
            flash("Could not save the book right now. Please try again.", "error")
            return redirect(url_for("add_book"))

    return render_template("add_book.html", nav_active="manage_books")


@app.route("/view-books")
@login_required
def view_books():
    try:
        books = get_all_books()
    except sqlite3.Error:
        flash("Could not load books right now. Please try again.", "error")
        books = []

    return render_template("view_books.html", books=books, nav_active="manage_books")


@app.route("/book/<int:id>")
@login_required
def book_detail(id):
    try:
        book = get_book_by_id(id)
    except sqlite3.Error:
        flash("Could not load book details right now. Please try again.", "error")
        return redirect(url_for("view_books"))

    if not book:
        flash("Book not found.", "error")
        return redirect(url_for("view_books"))

    return render_template("book_detail.html", book=book, nav_active="manage_books")


@app.route("/update-book")
@login_required
def update_book():
    return render_template("update_book.html", nav_active="manage_books")


@app.route("/search-books")
@login_required
def search_books():
    return render_template("search_books.html", nav_active="manage_books")


@app.route("/delete-book")
@login_required
def delete_book():
    flash("Delete book workflow can be connected here.", "success")
    return redirect(url_for("manage_books"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
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
            return redirect(url_for("profile"))

        try:
            if email_exists(email, exclude_user_id=user["id"]):
                flash("This email is already in use by another account.", "error")
                return redirect(url_for("profile"))

            hashed_password = None
            wants_password_change = any([current_password, new_password, confirm_password])
            if wants_password_change:
                if not current_password:
                    flash("Enter your current password to set a new password.", "error")
                    return redirect(url_for("profile"))
                if not check_password_hash(user["password"], current_password):
                    flash("Current password is incorrect.", "error")
                    return redirect(url_for("profile"))
                if not new_password:
                    flash("New password cannot be empty.", "error")
                    return redirect(url_for("profile"))
                if new_password != confirm_password:
                    flash("New password and confirm password do not match.", "error")
                    return redirect(url_for("profile"))
                hashed_password = generate_password_hash(new_password)

            update_user_profile(user["id"], name, email, hashed_password=hashed_password)
            refreshed_user = get_user_by_id(user["id"])
            if refreshed_user:
                set_user_session(refreshed_user)
            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))
        except sqlite3.Error:
            flash("Could not update your profile right now. Please try again.", "error")
            return redirect(url_for("profile"))

    return render_template(
        "profile.html",
        name=user["name"],
        email=user["email"],
        role=normalize_role(user["role"]),
        role_badge=role_badge_class(user["role"]),
        nav_active="profile",
    )


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


init_db()


if __name__ == "__main__":
    app.run(debug=True)
