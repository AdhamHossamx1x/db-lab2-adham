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


def get_db():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "registration"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("hello"))
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
    return redirect(url_for("hello"))


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

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT user_id, name, password_hash FROM users WHERE email = %s",
                (email,),
            )
            user = cur.fetchone()
    finally:
        db.close()

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
    return redirect(url_for("hello"))


@app.route("/hello")
@login_required
def hello():
    return render_template("hello.html", name=session["name"])


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
