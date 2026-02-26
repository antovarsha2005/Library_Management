import sqlite3
from flask import Flask, flash, redirect, render_template, request, url_for
from database import delete_user_by_id, get_connection, init_db, search_users_by_name

app = Flask(__name__)
app.secret_key = "module2-library-secret-key"


def fetch_user(user_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, email, password FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def fetch_all_users():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, email, password FROM users ORDER BY id DESC"
        ).fetchall()


def get_dashboard_stats():
    with get_connection() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    # Dummy value for now, as requested.
    total_books = 320
    active_members = total_users

    return {
        "total_users": total_users,
        "total_books": total_books,
        "active_members": active_members,
    }


@app.route("/")
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    stats = get_dashboard_stats()
    return render_template("dashboard.html", stats=stats)


@app.route("/manage-user")
def manage_user():
    return render_template("manage_user.html")


@app.route("/users/add", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("add_user.html", form_data=request.form)

        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, password),
                )
                conn.commit()

            flash("User added successfully.", "success")
            return redirect(url_for("view_users"))
        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different email.", "danger")
            return render_template("add_user.html", form_data=request.form)

    return render_template("add_user.html")


@app.route("/users")
def view_users():
    users = fetch_all_users()
    return render_template("view_users.html", users=users)


@app.route("/search-users", methods=["GET"])
def search_user():
    query = request.args.get("q", "").strip()
    users = search_users_by_name(query) if query else []
    return render_template("search_user.html", query=query, users=users)


@app.route("/users/<int:user_id>")
def user_detail(user_id):
    user = fetch_user(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("view_users"))
    return render_template("user_detail.html", user=user)


@app.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def update_user(user_id):
    user = fetch_user(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("view_users"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("update_user.html", user=user)

        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE users
                    SET name = ?, email = ?, password = ?
                    WHERE id = ?
                    """,
                    (name, email, password, user_id),
                )
                conn.commit()

            flash("User updated successfully.", "success")
            return redirect(url_for("view_users"))
        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different email.", "danger")
            refreshed_user = {"id": user_id, "name": name, "email": email, "password": password}
            return render_template("update_user.html", user=refreshed_user)

    return render_template("update_user.html", user=user)


@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    if delete_user_by_id(user_id):
        flash("User deleted successfully.", "success")
    else:
        flash("User not found.", "warning")
    return redirect(url_for("view_users"))


@app.route("/profile")
def profile():
    admin = {
        "name": "Library Admin",
        "email": "admin@library.com",
        "role": "System Administrator",
    }
    return render_template("profile.html", admin=admin)


@app.route("/logout", methods=["POST"])
def logout():
    flash("You have been logged out.", "info")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
