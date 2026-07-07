"""Acceso a la base de datos SQLite: creación de tablas, migraciones y
utilidades de usuarios admin."""
import logging
import sqlite3
import time
from datetime import datetime

from werkzeug.security import generate_password_hash

from config import DB_PATH, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_ROLE

logger = logging.getLogger(__name__)


def with_sqlite_retry(func, *args, retries=5, delay=0.5, **kwargs):
    """Reintenta una operación de SQLite si la base de datos está bloqueada
    (p. ej. varios workers de gunicorn arrancando a la vez)."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as exc:
            last_error = exc
            if "locked" in str(exc).lower():
                logger.warning(
                    "SQLite bloqueada (intento %s/%s), reintentando en %.1fs: %s",
                    attempt, retries, delay, exc,
                )
                time.sleep(delay)
                continue
            raise
    raise last_error


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
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


def migrate_user_roles():
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "role" not in columns:
            cursor.execute("ALTER TABLE admin_users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            conn.commit()


def migrate_registros_centro():
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(registros)")
        columns = [row[1] for row in cursor.fetchall()]
        if "centro" not in columns:
            cursor.execute("ALTER TABLE registros ADD COLUMN centro TEXT NOT NULL DEFAULT ''")
            conn.commit()


def get_admin_user(username):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, username, password_hash, role, created_at FROM admin_users WHERE username = ?",
            (username,)
        ).fetchone()
        return dict(row) if row else None


def create_default_admin():
    if not DEFAULT_ADMIN_USERNAME or not DEFAULT_ADMIN_PASSWORD:
        return
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
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
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
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


def init_app_db():
    """Punto único de entrada para inicializar/migrar la base de datos al
    arrancar la aplicación."""
    with_sqlite_retry(init_db)
    with_sqlite_retry(migrate_user_roles)
    with_sqlite_retry(migrate_registros_centro)
    with_sqlite_retry(create_default_admin)
