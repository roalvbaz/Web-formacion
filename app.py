"""Punto de entrada de la aplicación Flask.

Este archivo solo se encarga de:
- crear la app y configurarla,
- inicializar la base de datos,
- registrar los blueprints con las rutas (routes/),
- arrancar el servidor de desarrollo o exponer `app` para gunicorn.

La lógica está repartida en:
- config.py              constantes (rutas, respuestas válidas, centros...)
- db.py                   acceso a sqlite (init, migraciones, admin_users)
- auth.py                 decoradores de sesión/roles
- quiz.py                 corrección y validación del cuestionario
- certificates.py         generación del PDF del certificado
- routes/pages.py         páginas HTML (leídas desde public/)
- routes/auth_routes.py   login/logout/registro de admins
- routes/api.py           API de registros, sesión y administración
- routes/certificates_routes.py  descarga/generación de certificados
- routes/files_routes.py  descarga del PDF del curso (carpeta files/)

Estructura de carpetas esperada junto a este archivo:
    public/     -> todo el HTML/CSS/JS (index.html, styles.css, script.js...)
    files/      -> informacion.pdf
    database/   -> registros.db (se crea sola si no existe)
"""
import logging
import os
import sys

from flask import Flask

from config import PUBLIC_DIR, SECRET_KEY
from db import create_admin_user, init_app_db
from routes.api import api_bp
from routes.auth_routes import auth_bp
from routes.certificates_routes import certificates_bp
from routes.files_routes import files_bp
from routes.pages import pages_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# static_folder apunta SOLO a public/ (HTML/CSS/JS), no a la raíz del
# proyecto. Antes static_folder='.' exponía cualquier archivo del proyecto
# como estático (incluida la base de datos en database/registros.db si
# alguien pedía esa ruta directamente).
app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path='')
app.secret_key = SECRET_KEY
if app.secret_key == 'dev-change-this-secret':
    logger.warning(
        "SECRET_KEY no está definida en el entorno; usando un valor de desarrollo "
        "inseguro. Define la variable de entorno SECRET_KEY en producción."
    )

app.register_blueprint(pages_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(certificates_bp)
app.register_blueprint(files_bp)

try:
    init_app_db()
except Exception:
    logger.exception("Fallo al inicializar la base de datos en el arranque")
    raise


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
