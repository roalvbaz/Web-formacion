"""Endpoints de API: registros públicos, sesión, panel de admin y export CSV."""
import csv
import json
import sqlite3
from datetime import datetime
from io import StringIO

from flask import Blueprint, Response, jsonify, request, session

from auth import admin_required_api
from config import DB_PATH
from quiz import validate_registro_payload

api_bp = Blueprint("api", __name__)


def build_public_registros_query(filters):
    query = "SELECT id, nombre, dni, email, centro, score, fecha FROM registros WHERE aprobado = 1"
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


@api_bp.get("/api/registros")
def get_registros():
    filters = {
        'nombre': request.args.get('nombre', '').strip(),
        'dni': request.args.get('dni', '').strip(),
        'email': request.args.get('email', '').strip(),
        'centro': request.args.get('centro', '').strip(),
    }
    query, params = build_public_registros_query(filters)
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(row) for row in rows])


@api_bp.get("/api/session")
def get_session():
    role = session.get("user_role")
    return jsonify({
        "authenticated": bool(session.get("authenticated")),
        "username": session.get("username"),
        "user_role": str(role).lower() if role else None,
    })


@api_bp.post("/api/registro")
def create_registro():
    data = request.get_json(silent=True) or {}

    nombre, dni, email, centro, score, cleaned_respuestas = validate_registro_payload(data)
    if not nombre:
        return jsonify({"ok": False, "error": cleaned_respuestas}), 400

    aprobado = 1 if score > 14 else 0
    fecha = data.get("fecha") or datetime.now().isoformat(timespec="seconds")

    if not aprobado:
        return jsonify({"ok": False, "error": "No superó el mínimo de aciertos"}), 403

    with sqlite3.connect(DB_PATH, timeout=10) as conn:
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
        registro_id = cursor.lastrowid
        conn.commit()

    return jsonify({
        "ok": True,
        "message": "Registro guardado correctamente",
        "score": score,
        "id": registro_id,
    })


# --- Endpoints de administración: SOLO admins ---

@api_bp.get("/api/admin/users")
@admin_required_api
def get_admin_users():
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM admin_users ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@api_bp.delete("/api/admin/users/<int:user_id>")
@admin_required_api
def delete_admin_user(user_id):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
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


@api_bp.get("/api/admin/registros")
@admin_required_api
def get_all_registros():
    filters = {
        'dni': request.args.get('dni', '').strip(),
        'email': request.args.get('email', '').strip(),
        'centro': request.args.get('centro', '').strip(),
        'aprobado': request.args.get('aprobado', '').strip(),
    }
    query, params = build_admin_query(filters)
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(row) for row in rows])


@api_bp.delete("/api/admin/registros/<int:registro_id>")
@admin_required_api
def delete_registro(registro_id):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
        deleted = cursor.rowcount
        conn.commit()

    if deleted:
        return jsonify({"ok": True, "message": "Registro eliminado correctamente."})
    return jsonify({"ok": False, "error": "Registro no encontrado."}), 404


@api_bp.get("/api/export/csv")
@admin_required_api
def export_csv():
    filters = {
        'dni': request.args.get('dni', '').strip(),
        'email': request.args.get('email', '').strip(),
        'centro': request.args.get('centro', '').strip(),
        'aprobado': request.args.get('aprobado', '').strip(),
    }
    query, params = build_admin_query(filters)
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            query.replace(
                'SELECT id, nombre, dni, email, centro, score, aprobado, fecha, respuestas',
                'SELECT nombre, dni, email, centro, score, aprobado, fecha, respuestas'
            ),
            params
        ).fetchall()

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


@api_bp.get("/api/pdf")
def get_pdf_path():
    from config import PDF_PATH
    if PDF_PATH.exists():
        return jsonify({"path": str(PDF_PATH), "exists": True})
    return jsonify({"path": None, "exists": False})
