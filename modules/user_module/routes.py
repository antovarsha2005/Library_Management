from functools import wraps
import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from database import (
    ROLE_VALUES,
    build_admin_dashboard_stats,
    delete_user_by_id,
    get_connection,
    get_user_by_id,
    normalize_role,
    search_users_by_name,
)


user_bp = Blueprint("user", __name__)


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
            flash("Please log in to continue.", "danger")
            return redirect(url_for("login"))

        user = get_user_by_id(user_id)
        if not user:
            session.clear()
            flash("Session expired. Please log in again.", "danger")
            return redirect(url_for("login"))

        set_user_session(user)
        return route_function(*args, **kwargs)

    return wrapper


def admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Access denied.", "danger")
            return redirect(url_for("role_dashboard"))
        return route_function(*args, **kwargs)

    return wrapper


def fetch_user(user_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, email, password, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def fetch_all_users():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, email, password, role FROM users ORDER BY id DESC"
        ).fetchall()


@user_bp.route("/")
@login_required
@admin_required
def home():
    return redirect(url_for("user.dashboard"))


@user_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats = build_admin_dashboard_stats()
    return render_template("admin/dashboard.html", stats=stats)


@user_bp.route("/manage-user")
@login_required
@admin_required
def manage_user():
    return render_template("admin/manage_user.html")


@user_bp.route("/users/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role_input = request.form.get("role", "").strip()
        role = normalize_role(role_input)

        if not name or not email or not password or not role_input:
            flash("All fields are required.", "danger")
            return render_template("admin/add_user.html", form_data=request.form)

        if role not in ROLE_VALUES:
            flash("Please select a valid role.", "danger")
            return render_template("admin/add_user.html", form_data=request.form)

        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    (name, email, generate_password_hash(password), role),
                )
                conn.commit()

            flash("User added successfully.", "success")
            return redirect(url_for("user.view_users"))
        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different email.", "danger")
            return render_template("admin/add_user.html", form_data=request.form)

    return render_template("admin/add_user.html")


@user_bp.route("/users")
@login_required
@admin_required
def view_users():
    users = fetch_all_users()
    return render_template("admin/view_users.html", users=users)


@user_bp.route("/search-users", methods=["GET"])
@login_required
@admin_required
def search_user():
    query = request.args.get("q", "").strip()
    users = search_users_by_name(query) if query else []
    return render_template("admin/search_user.html", query=query, users=users)


@user_bp.route("/users/<int:user_id>")
@login_required
@admin_required
def user_detail(user_id):
    user = fetch_user(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("user.view_users"))
    return render_template("admin/user_detail.html", user=user)


@user_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def update_user(user_id):
    user = fetch_user(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("user.view_users"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role_input = request.form.get("role", "").strip()
        role = normalize_role(role_input)

        if not name or not email or not role_input:
            flash("Name, email, and role are required.", "danger")
            return render_template(
                "admin/update_user.html",
                user={"id": user_id, "name": name, "email": email, "role": role},
            )

        if role not in ROLE_VALUES:
            flash("Please select a valid role.", "danger")
            return render_template(
                "admin/update_user.html",
                user={"id": user_id, "name": name, "email": email, "role": role_input},
            )

        try:
            with get_connection() as conn:
                if password:
                    conn.execute(
                        """
                        UPDATE users
                        SET name = ?, email = ?, password = ?, role = ?
                        WHERE id = ?
                        """,
                        (name, email, generate_password_hash(password), role, user_id),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE users
                        SET name = ?, email = ?, role = ?
                        WHERE id = ?
                        """,
                        (name, email, role, user_id),
                    )
                conn.commit()

            flash("User updated successfully.", "success")
            return redirect(url_for("user.view_users"))
        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different email.", "danger")
            refreshed_user = {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role,
            }
            return render_template("admin/update_user.html", user=refreshed_user)

    return render_template("admin/update_user.html", user=user)


@user_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    if delete_user_by_id(user_id):
        flash("User deleted successfully.", "success")
    else:
        flash("User not found.", "warning")
    return redirect(url_for("user.view_users"))


@user_bp.route("/profile")
@login_required
@admin_required
def profile():
    admin = {
        "name": "Library Admin",
        "email": "admin@library.com",
        "role": "System Administrator",
    }
    return render_template("admin/profile.html", admin=admin)
