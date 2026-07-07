"""Decoradores de autenticación y autorización basados en la sesión Flask."""
from functools import wraps

from flask import jsonify, redirect, session


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


def admin_required_api(func):
    """Igual que admin_required pero devuelve JSON 401/403 en lugar de
    redirigir, pensado para endpoints de API consumidos por fetch/JS."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"ok": False, "error": "No autenticado."}), 401
        if session.get("user_role") != "admin":
            return jsonify({"ok": False, "error": "Permisos insuficientes."}), 403
        return func(*args, **kwargs)
    return wrapper
