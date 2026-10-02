"""ИС «КодСтарт» — запись на курсы программирования.

Поток: регистрация -> авторизация -> работа с заявками (пользователь)
и управление статусами заявок (администратор).
"""
import os
import re
from datetime import date
from functools import wraps

import pymysql
from flask import (Flask, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "kodstart"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

PAYMENT_METHODS = {"cash": "Наличные", "card": "Банковская карта", "transfer": "Перевод"}
PER_PAGE = 5

# --- правила валидации (одинаковые на клиенте и сервере) ---
RE_LOGIN = re.compile(r"^[A-Za-z0-9_]{4,30}$")
RE_FIO = re.compile(r"^[А-Яа-яЁё\- ]{5,150}$")
RE_PHONE = re.compile(r"^8\(\d{3}\)\d{3}-\d{2}-\d{2}$")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------ БД
def get_db():
    if "db" not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False, commit=False):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, args)
        if commit:
            db.commit()
            return cur.lastrowid
        return cur.fetchone() if one else cur.fetchall()


# ------------------------------------------------------------ доступ
def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Войдите в систему", "error")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Недостаточно прав", "error")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


# ------------------------------------------------------------ страницы
@app.route("/")
def index():
    courses = query("SELECT * FROM courses ORDER BY id")
    return render_template("index.html", courses=courses)


def validate_registration(form):
    errors = {}
    if not RE_LOGIN.match(form.get("login", "")):
        errors["login"] = "Логин: 4–30 символов, латиница, цифры, _"
    elif query("SELECT id FROM users WHERE login=%s", (form["login"],), one=True):
        errors["login"] = "Такой логин уже занят"
    if len(form.get("password", "")) < 6:
        errors["password"] = "Пароль — не менее 6 символов"
    if not RE_FIO.match(form.get("full_name", "").strip()):
        errors["full_name"] = "ФИО — только кириллица, пробелы и дефис"
    if not RE_PHONE.match(form.get("phone", "")):
        errors["phone"] = "Телефон в формате 8(XXX)XXX-XX-XX"
    if not RE_EMAIL.match(form.get("email", "")):
        errors["email"] = "Некорректный email"
    elif query("SELECT id FROM users WHERE email=%s", (form["email"],), one=True):
        errors["email"] = "Этот email уже зарегистрирован"
    return errors


@app.route("/register", methods=["GET", "POST"])
def register():
    errors, form = {}, {}
    if request.method == "POST":
        form = request.form
        errors = validate_registration(form)
        if not errors:
            query(
                "INSERT INTO users (login, password_hash, full_name, phone, email) "
                "VALUES (%s,%s,%s,%s,%s)",
                (form["login"], generate_password_hash(form["password"]),
                 form["full_name"].strip(), form["phone"], form["email"]),
                commit=True,
            )
            flash("Регистрация прошла успешно. Войдите в систему", "success")
            return redirect(url_for("login"))
    return render_template("register.html", errors=errors, form=form)


@app.route("/api/check-login")
def check_login():
    """Проверка уникальности логина на лету (AJAX)."""
    login_value = request.args.get("login", "")
    taken = bool(query("SELECT id FROM users WHERE login=%s", (login_value,), one=True))
    return jsonify({"available": not taken})


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = query("SELECT * FROM users WHERE login=%s", (request.form.get("login", ""),), one=True)
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear()
            session.update(user_id=user["id"], role=user["role"], name=user["full_name"])
            flash(f"Добро пожаловать, {user['full_name']}!", "success")
            return redirect(url_for("admin" if user["role"] == "admin" else "cabinet"))
        error = "Неверный логин или пароль"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из системы", "success")
    return redirect(url_for("index"))


@app.route("/cabinet", methods=["GET", "POST"])
@login_required()
def cabinet():
    errors = {}
    if request.method == "POST":
        f = request.form
        if not f.get("course_id", "").isdigit():
            errors["course_id"] = "Выберите курс"
        try:
            if date.fromisoformat(f.get("start_date", "")) < date.today():
                errors["start_date"] = "Дата не может быть в прошлом"
        except ValueError:
            errors["start_date"] = "Укажите дату начала"
        if f.get("payment_method") not in PAYMENT_METHODS:
            errors["payment_method"] = "Выберите способ оплаты"
        if not errors:
            query(
                "INSERT INTO applications (user_id, course_id, start_date, payment_method, comment) "
                "VALUES (%s,%s,%s,%s,%s)",
                (session["user_id"], f["course_id"], f["start_date"],
                 f["payment_method"], f.get("comment", "")[:255]),
                commit=True,
            )
            flash("Заявка отправлена", "success")
            return redirect(url_for("cabinet"))
    apps = query(
        "SELECT a.*, c.title, s.name AS status FROM applications a "
        "JOIN courses c ON c.id=a.course_id JOIN statuses s ON s.id=a.status_id "
        "WHERE a.user_id=%s ORDER BY a.created_at DESC",
        (session["user_id"],),
    )
    courses = query("SELECT id, title FROM courses ORDER BY title")
    return render_template("cabinet.html", apps=apps, courses=courses, errors=errors,
                           payments=PAYMENT_METHODS, today=date.today().isoformat())


@app.route("/admin")
@login_required(role="admin")
def admin():
    status_filter = request.args.get("status", "")
    search = request.args.get("q", "").strip()
    page = max(int(request.args.get("page", 1) or 1), 1)

    where, args = [], []
    if status_filter.isdigit():
        where.append("a.status_id=%s")
        args.append(status_filter)
    if search:
        where.append("(u.full_name LIKE %s OR c.title LIKE %s)")
        args += [f"%{search}%", f"%{search}%"]
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    base = (" FROM applications a JOIN users u ON u.id=a.user_id "
            "JOIN courses c ON c.id=a.course_id JOIN statuses s ON s.id=a.status_id ")

    total = query("SELECT COUNT(*) AS n" + base + where_sql, args, one=True)["n"]
    pages = max((total + PER_PAGE - 1) // PER_PAGE, 1)
    apps = query(
        "SELECT a.*, u.full_name, u.phone, c.title, s.name AS status" + base + where_sql +
        " ORDER BY a.created_at DESC LIMIT %s OFFSET %s",
        args + [PER_PAGE, (page - 1) * PER_PAGE],
    )
    statuses = query("SELECT * FROM statuses ORDER BY id")
    return render_template("admin.html", apps=apps, statuses=statuses, page=page,
                           pages=pages, total=total, status_filter=status_filter,
                           search=search, payments=PAYMENT_METHODS)


@app.route("/admin/status/<int:app_id>", methods=["POST"])
@login_required(role="admin")
def change_status(app_id):
    status_id = request.form.get("status_id", "")
    if not query("SELECT id FROM statuses WHERE id=%s", (status_id,), one=True):
        return jsonify({"ok": False, "message": "Неизвестный статус"}), 400
    query("UPDATE applications SET status_id=%s WHERE id=%s", (status_id, app_id), commit=True)
    query("INSERT INTO status_history (application_id, status_id, changed_by) VALUES (%s,%s,%s)",
          (app_id, status_id, session["user_id"]), commit=True)
    return jsonify({"ok": True, "message": f"Статус заявки №{app_id} обновлён"})


@app.template_filter("rudate")
def rudate(value):
    return value.strftime("%d.%m.%Y") if value else ""


if __name__ == "__main__":
    app.run(debug=True)
