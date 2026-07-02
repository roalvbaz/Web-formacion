import os
from flask import Flask, jsonify, request, send_file, Response, redirect, session
from datetime import datetime
from functools import wraps
from io import StringIO
import csv
import json
import sqlite3
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash
import sys

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-change-this-secret')
DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD')
DEFAULT_ADMIN_ROLE = os.environ.get('DEFAULT_ADMIN_ROLE', 'admin')
DB_PATH = Path(__file__).resolve().parent / "database" / "registros.db"
PDF_PATH = Path(__file__).resolve().parent / "files" / "informacion.pdf"

VALID_ANSWERS = {
    'p1': 'e',
    'p2': 'b',
    'p3': 'd',
    'p4': 'e',
    'p5': 'c',
    'p6a': 'fisico',
    'p6b': 'biologico',
    'p6c': 'quimico',
    'p6d': 'quimico',
    'p7': 'c',
    'p8': 'b',
    'p9': 'a',
    'p10': 'd',
    'p11': 'd',
    'p12': 'd',
    'p13': 'f',
    'p14': 'v',
    'p15': 'f',
    'p16': 'v',
    'p17': 'v',
    'p18': 'v',
    'p19': 'v',
    'p20': 'f',
    'p21': 'f',
    'p22': 'f',
    'p23': 'v',
    'p24': 'f',
    'p25': 'v',
    'p26': 'v',
}

REQUIRED_QUESTIONS = list(VALID_ANSWERS.keys())


def calculate_score(respuestas):
    score = 0
    cleaned = {}
    for question, answer in VALID_ANSWERS.items():
        value = str(respuestas.get(question, '')).strip()
        cleaned[question] = value
        if value == answer:
            score += 1
    return score, cleaned


def validate_registro_payload(data):
    nombre = (data.get('nombre') or '').strip()
    dni = (data.get('dni') or '').strip()
    email = (data.get('email') or '').strip()
    centro = (data.get('centro') or '').strip()
    respuestas = data.get('respuestas')

    if not nombre or not dni or not email or not centro:
        return None, None, None, None, None, 'Faltan datos obligatorios: nombre, dni, email y centro son requeridos.'

    if centro not in CENTROS:
        return None, None, None, None, None, 'Centro no válido. Selecciona uno de la lista.'

    if not isinstance(respuestas, dict):
        return None, None, None, None, None, 'El campo respuestas debe ser un objeto con todas las preguntas.'

    missing = [q for q in REQUIRED_QUESTIONS if not str(respuestas.get(q, '')).strip()]
    if missing:
        return None, None, None, None, None, f'Faltan respuestas para las preguntas: {", ".join(missing)}.'

    score, cleaned_respuestas = calculate_score(respuestas)
    return nombre, dni, email, centro, score, cleaned_respuestas


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect("/admin/login")
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect("/admin/login")
        if session.get("user_role") != "admin":
            return redirect("/")
        return func(*args, **kwargs)
    return wrapper


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dni TEXT NOT NULL,
            email TEXT NOT NULL,
            centro TEXT NOT NULL,
            score INTEGER NOT NULL,
            aprobado INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            respuestas TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_admin_user(username):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, username, password_hash, role, created_at FROM admin_users WHERE username = ?",
            (username,)
        ).fetchone()
        return dict(row) if row else None


def create_default_admin():
    if not DEFAULT_ADMIN_USERNAME or not DEFAULT_ADMIN_PASSWORD:
        return
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM admin_users")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute(
                "INSERT INTO admin_users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (
                    DEFAULT_ADMIN_USERNAME,
                    generate_password_hash(DEFAULT_ADMIN_PASSWORD),
                    DEFAULT_ADMIN_ROLE,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()


def create_admin_user(username, password, role='user'):
    if not username or not password:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO admin_users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (
                    username,
                    generate_password_hash(password),
                    role,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


CENTROS = [
    'CD Zegama',
    'CD Legazpi',
    'CD Alda',
    'Segura',
    'Irun',
    'Egia',
    'URTMS Victoria Enea',
    'Legazpi',
    'Aretxabaleta',
    'SSGG',
    'Egiluze',
    'Bilbao',
    'Sopuerta',
    'Markina',
    'Otxandio',
    'Orozko',
    'Arrotegi',
    'Oizpe',
    'Trucios',
    'Urduliz',
    'Bernedo',
    'Lodosa',
    'Andosilla',
    'Mendabia',
    'Unx',
    'Montesclaros',
    'Cicero',
]

def migrate_user_roles():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "role" not in columns:
            cursor.execute("ALTER TABLE admin_users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            conn.commit()


def migrate_registros_centro():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(registros)")
        columns = [row[1] for row in cursor.fetchall()]
        if "centro" not in columns:
            cursor.execute("ALTER TABLE registros ADD COLUMN centro TEXT NOT NULL DEFAULT ''")
            conn.commit()


init_db()
migrate_user_roles()
migrate_registros_centro()
create_default_admin()


@app.get("/")
@login_required
def index():
    return send_file(Path(__file__).resolve().parent / "index.html")


@app.get("/login")
def login_alias():
    return redirect("/admin/login")


@app.get("/login/")
def login_alias_slash():
    return redirect("/login")


def build_public_registros_query(filters):
    query = "SELECT nombre, dni, email, centro, score, fecha FROM registros WHERE aprobado = 1"
    params = []

    if filters.get('nombre'):
        query += " AND LOWER(nombre) LIKE ?"
        params.append(f"%{filters['nombre'].lower()}%")

    if filters.get('dni'):
        query += " AND LOWER(dni) LIKE ?"
        params.append(f"%{filters['dni'].lower()}%")

    if filters.get('email'):
        query += " AND LOWER(email) LIKE ?"
        params.append(f"%{filters['email'].lower()}%")

    if filters.get('centro'):
        query += " AND LOWER(centro) LIKE ?"
        params.append(f"%{filters['centro'].lower()}%")

    query += " ORDER BY id DESC"
    return query, params


@app.get("/api/registros")
def get_registros():
    filters = {
        'nombre': request.args.get('nombre', '').strip(),
        'dni': request.args.get('dni', '').strip(),
        'email': request.args.get('email', '').strip(),
        'centro': request.args.get('centro', '').strip(),
    }
    query, params = build_public_registros_query(filters)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/session")
def get_session():
    role = session.get("user_role")
    return jsonify({
        "authenticated": bool(session.get("authenticated")),
        "username": session.get("username"),
        "user_role": str(role).lower() if role else None,
    })


@app.post("/api/registro")
def create_registro():
    data = request.get_json(silent=True) or {}

    nombre = (data.get("nombre") or "").strip()
    dni = (data.get("dni") or "").strip()
    email = (data.get("email") or "").strip()
    score = int(data.get("score", 0))
    aprobado = 1 if score > 14 else 0
    fecha = data.get("fecha") or datetime.now().isoformat(timespec="seconds")
    respuestas = data.get("respuestas") or {}

    nombre, dni, email, centro, score, cleaned_respuestas = validate_registro_payload(data)
    if not nombre:
        return jsonify({"ok": False, "error": cleaned_respuestas}), 400

    aprobado = 1 if score > 14 else 0
    fecha = data.get("fecha") or datetime.now().isoformat(timespec="seconds")

    if not aprobado:
        return jsonify({"ok": False, "error": "No superó el mínimo de aciertos"}), 403

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO registros (nombre, dni, email, centro, score, aprobado, fecha, respuestas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nombre,
                dni,
                email,
                centro,
                score,
                aprobado,
                fecha,
                json.dumps(cleaned_respuestas, ensure_ascii=False),
            ),
        )
    return jsonify({"ok": True, "message": "Registro guardado correctamente", "score": score})


@app.get("/admin")
@admin_required
def admin_dashboard():
    return send_file(Path(__file__).resolve().parent / "admin.html")


@app.get("/admin/")
def admin_dashboard_slash():
    return redirect("/admin")


@app.get("/admin_login")
def admin_login_alias():
    return redirect("/admin/login")


@app.get("/admin/login")
def admin_login_page():
    if session.get("authenticated"):
        if session.get("user_role") == "admin":
            return redirect("/admin")
        return redirect("/")
    return send_file(Path(__file__).resolve().parent / "login.html")


@app.get("/admin/login/")
def admin_login_page_slash():
    return redirect("/admin/login")


@app.get("/admin/register")
@admin_required
def admin_register_page():
    return send_file(Path(__file__).resolve().parent / "register.html")


@app.get("/admin/users")
@admin_required
def admin_users_page():
    return send_file(Path(__file__).resolve().parent / "users.html")


@app.post("/admin/register")
@admin_required
def admin_register():
    username = (request.form.get("username", "") or "").strip()
    password = request.form.get("password", "") or ""
    password_confirm = request.form.get("password_confirm", "") or ""
    role = (request.form.get("role", "user") or "user").strip().lower()

    if role not in ("admin", "user"):
        role = "user"

    if not username or not password or not password_confirm:
        return redirect("/admin/register?error=Todos los campos son obligatorios.")

    if password != password_confirm:
        return redirect("/admin/register?error=Las contraseñas no coinciden.")

    if create_admin_user(username, password, role):
        return redirect("/admin/register?success=1")

    return redirect("/admin/register?error=El usuario ya existe.")


@app.get("/dashboard")
@login_required
def dashboard():
    return send_file(Path(__file__).resolve().parent / "dashboard.html")


@app.get("/dashboard/")
def dashboard_slash():
    return redirect("/dashboard")


@app.post("/admin/login")
def admin_login():
    username = (request.form.get("username", "") or "").strip()
    password = request.form.get("password", "") or ""
    user = get_admin_user(username)
    if user and check_password_hash(user["password_hash"], password):
        session["authenticated"] = True
        session["username"] = username
        session["user_role"] = str(user.get("role", "user")).lower()
        if session["user_role"] == "admin":
            return redirect("/admin")
        return redirect("/")
    return redirect("/admin/login?error=1")


@app.get("/admin/logout")
def admin_logout():
    session.pop("authenticated", None)
    session.pop("username", None)
    session.pop("user_role", None)
    return redirect("/admin/login")


@app.get("/api/admin/users")
@login_required
def get_admin_users():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM admin_users ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.delete("/api/admin/users/<int:user_id>")
@login_required
def delete_admin_user(user_id):
    if session.get("user_role") != "admin":
        return jsonify({"ok": False, "error": "Permisos insuficientes."}), 403

    username = session.get("username")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM admin_users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Usuario no encontrado."}), 404
        if row[0] == "admin":
            return jsonify({"ok": False, "error": "No se puede eliminar un administrador desde este panel."}), 403
        cursor.execute("DELETE FROM admin_users WHERE id = ?", (user_id,))
        conn.commit()

    return jsonify({"ok": True, "message": "Usuario eliminado correctamente."})


def build_admin_query(filters):
    query = "SELECT id, nombre, dni, email, centro, score, aprobado, fecha, respuestas FROM registros WHERE 1=1"
    params = []

    if filters.get('dni'):
        query += " AND LOWER(dni) LIKE ?"
        params.append(f"%{filters['dni'].lower()}%")

    if filters.get('email'):
        query += " AND LOWER(email) LIKE ?"
        params.append(f"%{filters['email'].lower()}%")

    if filters.get('centro'):
        query += " AND LOWER(centro) LIKE ?"
        params.append(f"%{filters['centro'].lower()}%")

    if filters.get('aprobado') in ('0', '1'):
        query += " AND aprobado = ?"
        params.append(int(filters['aprobado']))

    query += " ORDER BY id DESC"
    return query, params


@app.get("/api/admin/registros")
@login_required
def get_all_registros():
    filters = {
        'dni': request.args.get('dni', '').strip(),
        'email': request.args.get('email', '').strip(),
        'centro': request.args.get('centro', '').strip(),
        'aprobado': request.args.get('aprobado', '').strip(),
    }
    query, params = build_admin_query(filters)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(row) for row in rows])


@app.delete("/api/admin/registros/<int:registro_id>")
@login_required
def delete_registro(registro_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
        deleted = cursor.rowcount
        conn.commit()

    if deleted:
        return jsonify({"ok": True, "message": "Registro eliminado correctamente."})
    return jsonify({"ok": False, "error": "Registro no encontrado."}), 404


@app.get("/api/export/csv")
@login_required
def export_csv():
    filters = {
        'dni': request.args.get('dni', '').strip(),
        'email': request.args.get('email', '').strip(),
        'centro': request.args.get('centro', '').strip(),
        'aprobado': request.args.get('aprobado', '').strip(),
    }
    query, params = build_admin_query(filters)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query.replace('SELECT id, nombre, dni, email, centro, score, aprobado, fecha, respuestas', 'SELECT nombre, dni, email, centro, score, aprobado, fecha, respuestas'), params).fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre", "DNI", "Correo", "Centro", "Puntuación", "Aprobado", "Fecha", "Respuestas"])
    for row in rows:
        writer.writerow([
            row["nombre"],
            row["dni"],
            row["email"],
            row["centro"],
            row["score"],
            "Sí" if row["aprobado"] else "No",
            row["fecha"],
            row["respuestas"],
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=registros.csv"
    return response


@app.get("/api/pdf")
def get_pdf_path():
    if PDF_PATH.exists():
        return jsonify({"path": str(PDF_PATH), "exists": True})
    return jsonify({"path": None, "exists": False})


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "create-admin":
        if len(sys.argv) != 4:
            print("Uso: python app.py create-admin <usuario> <password>")
            sys.exit(1)
        username = sys.argv[2]
        password = sys.argv[3]
        if create_admin_user(username, password):
            print(f"Admin creado: {username}")
            sys.exit(0)
        print(f"No se pudo crear el admin. El usuario {username} puede ya existir.")
        sys.exit(1)

    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
