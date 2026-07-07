"""Ruta explícita para servir archivos descargables/consultables (el PDF del
curso), sin exponer el resto del proyecto como estático."""
from flask import Blueprint, abort, send_from_directory

from config import FILES_DIR

files_bp = Blueprint("files", __name__)


@files_bp.get("/files/<path:filename>")
def serve_file(filename):
    # send_from_directory ya previene el path traversal (../..), pero se
    # valida igualmente que el archivo resultante quede dentro de FILES_DIR.
    try:
        return send_from_directory(FILES_DIR, filename)
    except FileNotFoundError:
        abort(404)
