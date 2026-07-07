"""Configuración y constantes compartidas por toda la aplicación."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Carpeta con todo el HTML/CSS/JS servido al navegador (antes estaba mezclado
# en la raíz del proyecto). Se usa como static_folder de Flask.
PUBLIC_DIR = BASE_DIR / "public"

# Carpeta con archivos descargables/consultables (el PDF del curso). Se sirve
# mediante una ruta explícita en vez de exponer toda la raíz como estático.
FILES_DIR = BASE_DIR / "files"

DB_PATH = BASE_DIR / "database" / "registros.db"
PDF_PATH = FILES_DIR / "informacion.pdf"

# Carpeta con imágenes para el certificado (logo, firma escaneada...).
# Los archivos son opcionales: si no existen, el certificado se genera igual.
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
FIRMA_PATH = ASSETS_DIR / "firma.bmp"

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-change-this-secret')

DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD')
DEFAULT_ADMIN_ROLE = os.environ.get('DEFAULT_ADMIN_ROLE', 'admin')

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

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

CENTROS = [
    'CD Zegama',
    'CD Legazpi',
    'CD Alda',
    'Segura',
    'Irun',
    'Egia',
    'URTMS Victoria Enea',
    'Legazpi',
    'Debagioena',
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
    'Mendavia',
    'Unx',
    'Montesclaros',
    'Cicero',
]
