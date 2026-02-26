from functools import wraps
from pathlib import Path
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# SECURITY: replace with an environment value in production.
app.secret_key = "change-this-secret-key-in-production"

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


def role_badge_class(role):
    """Map role to a CSS class used by profile/dashboard role badges."""
    safe_role = normalize_role(role).lower()
    return f"badge-{safe_role}"


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


def set_user_session(user):
    """Persist user identity in session after login/profile update."""
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["role"] = normalize_role(user["role"])


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
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    flash("This email is already registered. Please use a different one.", "error")
                    return redirect(url_for("signup"))

                hashed_password = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    (name, email, hashed_password, role),
                )
                conn.commit()

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
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, email, password, role FROM users WHERE email = ?",
                    (email,),
                )
                user = cursor.fetchone()

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
    )


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
            with get_db() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT id FROM users WHERE email = ? AND id != ?",
                    (email, user["id"]),
                )
                if cursor.fetchone():
                    flash("This email is already in use by another account.", "error")
                    return redirect(url_for("profile"))

                update_fields = ["name = ?", "email = ?"]
                update_values = [name, email]

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

                    update_fields.append("password = ?")
                    update_values.append(generate_password_hash(new_password))

                update_values.append(user["id"])
                cursor.execute(
                    f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?",
                    tuple(update_values),
                )
                conn.commit()

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
