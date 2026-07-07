"""Endpoints para generar y descargar certificados PDF."""
import logging
import sqlite3
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from auth import admin_required_api
from certificates import generate_certificate_pdf
from config import DB_PATH

logger = logging.getLogger(__name__)

certificates_bp = Blueprint("certificates", __name__)


# NOTA DE SEGURIDAD: este endpoint es público (se usa justo después de que el
# alumno completa el test, sin haber iniciado sesión de admin), pero antes
# cualquiera podía descargar el certificado de otra persona simplemente
# probando IDs consecutivos (/api/certificate/1, /2, /3...), exponiendo
# nombre y DNI de terceros. Para mitigar esto sin romper el flujo público,
# se exige que el DNI del registro coincida con un parámetro `dni` enviado
# por el cliente (que el frontend ya conoce, porque el propio usuario lo
# introdujo en el formulario).
@certificates_bp.get("/api/certificate/<int:registro_id>")
def get_certificate(registro_id):
    """Genera y descarga el certificado PDF para un registro aprobado"""
    dni_solicitado = (request.args.get("dni") or "").strip()
    if not dni_solicitado:
        return jsonify({"ok": False, "error": "Falta el parámetro dni."}), 400

    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT nombre, dni, centro, fecha, aprobado FROM registros WHERE id = ?",
            (registro_id,)
        ).fetchone()

    if not row:
        return jsonify({"ok": False, "error": "Registro no encontrado"}), 404

    if row["dni"].strip().lower() != dni_solicitado.lower():
        # Mismo mensaje que "no encontrado" para no filtrar si el ID existe.
        return jsonify({"ok": False, "error": "Registro no encontrado"}), 404

    if not row["aprobado"]:
        return jsonify({"ok": False, "error": "Este registro no ha sido aprobado"}), 403

    pdf_buffer = generate_certificate_pdf(
        nombre=row["nombre"],
        dni=row["dni"],
        centro=row["centro"],
        fecha=row["fecha"]
    )

    filename = f"Certificado_{row['nombre'].replace(' ', '_')}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@certificates_bp.post("/api/certificate/generate")
@admin_required_api
def generate_certificate():
    """Genera un certificado PDF con los datos proporcionados.

    Restringido a administradores: antes era un endpoint público que permitía
    generar un "certificado de aprobación" con CUALQUIER nombre/DNI/centro,
    sin ninguna verificación contra la base de datos.
    """
    data = request.get_json(silent=True) or {}

    nombre = (data.get("nombre") or "").strip()
    dni = (data.get("dni") or "").strip()
    centro = (data.get("centro") or "").strip()
    fecha = data.get("fecha") or datetime.now().isoformat(timespec="seconds")

    if not nombre or not dni or not centro:
        return jsonify({"ok": False, "error": "Faltan datos: nombre, dni y centro son requeridos"}), 400

    try:
        pdf_buffer = generate_certificate_pdf(nombre, dni, centro, fecha)
        filename = f"Certificado_{nombre.replace(' ', '_')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.exception("Error generando certificado PDF")
        return jsonify({"ok": False, "error": f"Error al generar el certificado: {str(e)}"}), 500
