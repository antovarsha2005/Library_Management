import sqlite3

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config, DATABASE_PATH
from database import (
    ROLE_VALUES,
    SIGNUP_ROLES,
    create_user,
    email_exists,
    get_user_by_email,
    get_user_by_id,
    init_db,
    normalize_role,
)
from modules.book_module.routes import book_bp
from modules.transaction_module.routes import transaction_bp
from modules.user_module.routes import user_bp


app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config["SECRET_KEY"]
print("Database location:", DATABASE_PATH)


def set_user_session(user):
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["role"] = normalize_role(user["role"])


def password_matches(stored_password, provided_password):
    if not stored_password:
        return False

    try:
        if check_password_hash(stored_password, provided_password):
            return True
    except ValueError:
        pass

    return stored_password == provided_password


def role_endpoint(role):
    role_value = normalize_role(role)
    if role_value == "admin":
        return "user.dashboard"
    if role_value == "librarian":
        return "book.dashboard"
    return "transaction.dashboard"


def role_redirect():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))

    set_user_session(user)
    return redirect(url_for(role_endpoint(session.get("role"))))


@app.route("/")
def index():
    if session.get("user_id"):
        return role_redirect()
    return redirect(url_for("login"))


@app.route("/dashboard")
def role_dashboard():
    return role_redirect()


@app.route("/auth/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return role_redirect()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "").strip()

        if not all([name, email, password, confirm_password, role]):
            flash("Name, email, password, confirm password, and role are required.", "error")
            return redirect(url_for("signup"))

        role_value = normalize_role(role)
        if role_value not in ROLE_VALUES:
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
            create_user(name, email, hashed_password, role_value)

            flash("Signup successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("This email is already registered. Please use a different one.", "error")
            return redirect(url_for("signup"))
        except sqlite3.Error:
            flash("Unable to create your account right now. Please try again.", "error")
            return redirect(url_for("signup"))

    return render_template("auth/signup.html", roles=SIGNUP_ROLES)


@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return role_redirect()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("login"))

        try:
            user = get_user_by_email(email)
            if not user or not password_matches(user["password"], password):
                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))

            set_user_session(user)
            flash("Welcome back.", "success")
            return redirect(url_for(role_endpoint(session.get("role"))))
        except sqlite3.Error:
            flash("Unable to log in right now. Please try again.", "error")
            return redirect(url_for("login"))

    return render_template("auth/login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()

    if request.is_json:
        return jsonify({"message": "Logged out"}), 200

    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


app.register_blueprint(book_bp, url_prefix="/librarian")
app.register_blueprint(user_bp, url_prefix="/admin")
app.register_blueprint(transaction_bp, url_prefix="/user")

init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
