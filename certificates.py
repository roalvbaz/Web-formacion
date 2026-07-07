"""Generación del PDF de certificado de aprobación."""
from datetime import datetime
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from config import FIRMA_PATH, LOGO_PATH, MESES_ES


def _draw_image_fit(c, image_path, x, y, max_width, max_height, align="left"):
    """Dibuja una imagen dentro de una caja (max_width x max_height) sin
    deformarla, manteniendo su proporción original. `x, y` es la esquina
    inferior izquierda de la caja disponible.

    Si el archivo no existe o no se puede leer, no dibuja nada (el
    certificado sigue generándose con normalidad).
    """
    if not image_path.exists():
        return False

    try:
        img = ImageReader(str(image_path))
        img_width, img_height = img.getSize()
    except Exception:
        return False

    scale = min(max_width / img_width, max_height / img_height)
    draw_width = img_width * scale
    draw_height = img_height * scale

    if align == "center":
        draw_x = x + (max_width - draw_width) / 2
    else:
        draw_x = x

    # mask='auto' respeta la transparencia si el PNG tiene canal alfa.
    c.drawImage(
        img,
        draw_x,
        y,
        width=draw_width,
        height=draw_height,
        mask='auto',
        preserveAspectRatio=True,
    )
    return True


def generate_certificate_pdf(nombre, dni, centro, fecha):
    """Genera un certificado PDF de aprobación del curso de Manipulación de Alimentos"""
    buffer = BytesIO()

    # Usar tamaño A4 horizontal (landscape)
    page_width, page_height = landscape(A4)

    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    c.setTitle(f"Certificado - {nombre}")

    # Colores
    color_verde = HexColor("#2d5016")
    color_gris = HexColor("#d3d3d3")

    # Fondo gris claro
    c.setFillColor(color_gris)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # Encabezado con fondo verde
    c.setFillColor(color_verde)
    c.rect(0, page_height - 2*cm, page_width, 2*cm, fill=1, stroke=0)

    # Título "GSR" (o el logo, si existe assets/logo.png)
    logo_dibujado = _draw_image_fit(
        c,
        LOGO_PATH,
        x=2*cm,
        y=page_height - 1.9*cm,
        max_width=4*cm,
        max_height=1.6*cm,
        align="left",
    )
    if not logo_dibujado:
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor("white")
        c.drawString(2*cm, page_height - 1.3*cm, "GSR")

        # Subtítulo (solo si no hay logo, para no solaparse con la imagen)
        c.setFont("Helvetica", 8)
        c.drawString(2*cm, page_height - 1.7*cm, "GESTIÓN")
        c.drawString(2*cm, page_height - 1.95*cm, "SERVICIOS RESIDENCIALES")

    # Línea decorativa
    c.setStrokeColor(color_verde)
    c.setLineWidth(2)
    c.line(0, page_height - 2.2*cm, page_width, page_height - 2.2*cm)

    # Título principal
    c.setFillColor("black")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(page_width/2, page_height - 3.5*cm, "Ziurtatzea du / Certifica que:")

    # Cuerpo del certificado
    y_position = page_height - 4.8*cm

    # Nombre
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(color_verde)
    nombre_text = nombre.upper()
    c.drawCentredString(page_width/2, y_position, nombre_text)

    # DNI
    y_position -= 0.8*cm
    c.setFont("Helvetica", 14)
    c.drawCentredString(page_width/2, y_position, dni)

    # Texto de aprobación
    y_position -= 1.2*cm
    c.setFont("Helvetica", 11)
    c.setFillColor("black")
    c.drawCentredString(page_width/2, y_position, "Ha superado con éxito el curso Online de / Online ikastaroa gainditu du:")

    # Nombre del curso
    y_position -= 0.7*cm
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(color_verde)
    c.drawCentredString(page_width/2, y_position, "Curso Online GSR Manipulación de Alimentos")

    # Centro
    y_position -= 1.2*cm
    c.setFont("Helvetica", 10)
    c.setFillColor("black")
    c.drawCentredString(page_width/2, y_position, f"Centro: {centro}")

    # Fecha (formateada manualmente en español para no depender del locale del SO)
    y_position -= 0.6*cm
    try:
        fecha_obj = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        mes_nombre = MESES_ES[fecha_obj.month - 1]
        fecha_formateada = f"{fecha_obj.day} de {mes_nombre} de {fecha_obj.year}"
    except Exception:
        fecha_formateada = fecha

    c.setFont("Helvetica", 10)
    c.drawCentredString(page_width/2, y_position, f"Fecha: {fecha_formateada}")

    # Línea para firma
    y_position -= 1.5*cm
    c.setLineWidth(1)
    c.line(1.5*cm, y_position, 4.5*cm, y_position)
    c.setFont("Helvetica", 9)
    c.drawCentredString(3*cm, y_position - 0.4*cm, "Firma / Sinadura")

    # Firma escaneada (opcional), apoyada justo encima de la línea
    _draw_image_fit(
        c,
        FIRMA_PATH,
        x=1.5*cm,
        y=y_position + 0.1*cm,
        max_width=3*cm,
        max_height=1.2*cm,
        align="center",
    )

    # Pie de página
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#666666"))
    c.drawString(1*cm, 0.5*cm, "Emitido por GSR - Gestión Servicios Residenciales")

    c.save()
    buffer.seek(0)
    return buffer
