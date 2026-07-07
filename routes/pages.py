"""Rutas que sirven las páginas HTML (no-API)."""
from flask import Blueprint, redirect, send_file, session

from auth import admin_required, login_required
from config import PUBLIC_DIR

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
@login_required
def index():
    return send_file(PUBLIC_DIR / "index.html")


@pages_bp.get("/login")
def login_alias():
    return redirect("/admin/login")


@pages_bp.get("/login/")
def login_alias_slash():
    return redirect("/login")


@pages_bp.get("/admin")
@admin_required
def admin_dashboard():
    return send_file(PUBLIC_DIR / "admin.html")


@pages_bp.get("/admin/")
def admin_dashboard_slash():
    return redirect("/admin")


@pages_bp.get("/admin_login")
def admin_login_alias():
    return redirect("/admin/login")


@pages_bp.get("/admin/login")
def admin_login_page():
    if session.get("authenticated"):
        if session.get("user_role") == "admin":
            return redirect("/admin")
        return redirect("/")
    return send_file(PUBLIC_DIR / "login.html")


@pages_bp.get("/admin/login/")
def admin_login_page_slash():
    return redirect("/admin/login")


@pages_bp.get("/admin/register")
@admin_required
def admin_register_page():
    return send_file(PUBLIC_DIR / "register.html")


@pages_bp.get("/admin/users")
@admin_required
def admin_users_page():
    return send_file(PUBLIC_DIR / "users.html")


@pages_bp.get("/dashboard")
@login_required
def dashboard():
    return send_file(PUBLIC_DIR / "dashboard.html")


@pages_bp.get("/dashboard/")
def dashboard_slash():
    return redirect("/dashboard")
