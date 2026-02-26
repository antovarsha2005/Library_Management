from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"

DATABASE = "library.db"


def get_db():
    """Return a SQLite connection with row access by column name."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create required tables if they do not exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'LIBRARIAN',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


init_db()


def login_required(route_function):
    """Require an authenticated session for a route."""

    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return route_function(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not all([name, email, password]):
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    flash("Email already registered. Please log in.", "error")
                    return redirect(url_for("login"))

                hashed_password = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    (name, email, hashed_password, "LIBRARIAN"),
                )
                conn.commit()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("login"))
        except Exception:
            flash("Unable to create account right now. Please try again.", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not all([email, password]):
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

            if user["role"] != "LIBRARIAN":
                flash("Only librarian accounts can access this system.", "error")
                return redirect(url_for("login"))

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = "LIBRARIAN"

            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        except Exception:
            flash("Unable to log in right now. Please try again.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        name=session.get("user_name", "Librarian"),
        email=session.get("user_email", ""),
    )


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
