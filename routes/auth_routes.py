"""Rutas de autenticación: login, logout y alta de usuarios admin."""
from flask import Blueprint, redirect, request, session
from werkzeug.security import check_password_hash

from auth import admin_required
from db import create_admin_user, get_admin_user

auth_bp = Blueprint("auth_routes", __name__)


@auth_bp.post("/admin/register")
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


@auth_bp.post("/admin/login")
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


@auth_bp.get("/admin/logout")
def admin_logout():
    session.pop("authenticated", None)
    session.pop("username", None)
    session.pop("user_role", None)
    return redirect("/admin/login")
