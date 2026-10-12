import os
import re
from functools import wraps

import bcrypt
import pymysql
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
TITLE_MAX = 200


def get_db():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "registration"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def run(sql, params=(), fetch=False):
    """Run one SQL statement. Every value goes in params, never in the text."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall() if fetch else None
        db.commit()
        return rows
    finally:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def check_title(raw):
    title = raw.strip()
    if not title:
        return title, "Title is required"
    if len(title) > TITLE_MAX:
        return title, "Title is too long (200 characters at most)"
    return title, None


def show_todos(errors=None, new_title=""):
    todos = run(
        "SELECT todo_id, title, is_done, created_at FROM todos "
        "WHERE user_id = %s ORDER BY todo_id DESC",
        (session["user_id"],),
        fetch=True,
    )
    return render_template(
        "todos.html",
        todos=todos,
        errors=errors or [],
        new_title=new_title,
        name=session["name"],
    )


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("todo_list"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", errors=[], name="", email="")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    errors = []
    if not name:
        errors.append("Name is required")
    elif len(name) > 100:
        errors.append("Name is too long (100 characters at most)")
    if not email:
        errors.append("Email is required")
    elif len(email) > 255 or not EMAIL_PATTERN.match(email):
        errors.append("Email is not valid")
    if not password:
        errors.append("Password is required")
    elif len(password.encode("utf-8")) > 72:
        errors.append("Password is too long (72 characters at most)")
    if not confirm:
        errors.append("Confirm password is required")
    elif password and confirm != password:
        errors.append("Passwords do not match")

    if errors:
        return render_template("register.html", errors=errors, name=name, email=email)

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                (email, name, password_hash),
            )
            new_id = cur.lastrowid
        db.commit()
    except pymysql.err.IntegrityError as e:
        if e.args and e.args[0] == 1062:
            return render_template(
                "register.html", errors=["Email Already Exists"], name=name, email=email
            )
        raise
    finally:
        db.close()

    session.clear()
    session["user_id"] = new_id
    session["name"] = name
    return redirect(url_for("todo_list"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", errors=[], email="")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    errors = []
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if errors:
        return render_template("login.html", errors=errors, email=email)

    rows = run(
        "SELECT user_id, name, password_hash FROM users WHERE email = %s",
        (email,),
        fetch=True,
    )
    user = rows[0] if rows else None

    ok = False
    if user is not None and len(password.encode("utf-8")) <= 72:
        ok = bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8"))

    if not ok:
        return render_template(
            "login.html", errors=["Invalid email or password"], email=email
        )

    session.clear()
    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    return redirect(url_for("todo_list"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- To-do list (every query filters by the logged-in user) ----------

@app.route("/todos")
@login_required
def todo_list():
    return show_todos()


@app.route("/todos/add", methods=["POST"])
@login_required
def add_todo():
    title, error = check_title(request.form.get("title", ""))
    if error:
        return show_todos([error], new_title=title)
    run(
        "INSERT INTO todos (user_id, title) VALUES (%s, %s)",
        (session["user_id"], title),
    )
    return redirect(url_for("todo_list"))


@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
@login_required
def edit_todo(todo_id):
    title, error = check_title(request.form.get("title", ""))
    if error:
        return show_todos([error])
    run(
        "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
        (title, todo_id, session["user_id"]),
    )
    return redirect(url_for("todo_list"))


@app.route("/todos/<int:todo_id>/toggle", methods=["POST"])
@login_required
def toggle_todo(todo_id):
    is_done = 1 if request.form.get("is_done") == "1" else 0
    run(
        "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
        (is_done, todo_id, session["user_id"]),
    )
    return redirect(url_for("todo_list"))


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
@login_required
def delete_todo(todo_id):
    run(
        "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
        (todo_id, session["user_id"]),
    )
    return redirect(url_for("todo_list"))


if __name__ == "__main__":
    app.run(debug=True)
