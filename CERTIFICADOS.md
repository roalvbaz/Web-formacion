# Generación de Certificados PDF

Se han agregado nuevos endpoints para generar certificados PDF de aprobación del curso "Manipulación de Alimentos".

## Endpoints Disponibles

### 1. Generar Certificado desde un Registro Aprobado

**URL:** `GET /api/certificate/<registro_id>`

**Descripción:** Genera y descarga un certificado PDF para un registro que ya está en la base de datos y ha sido aprobado.

**Parámetros:**
- `registro_id` (integer): ID del registro en la base de datos

**Ejemplo:**
```bash
curl http://localhost:5000/api/certificate/1 --output certificado.pdf
```

**Respuestas:**
- **200 OK**: Descarga el archivo PDF
- **404 Not Found**: Si el registro no existe
- **403 Forbidden**: Si el registro no ha sido aprobado

---

### 2. Generar Certificado con Datos Personalizados

**URL:** `POST /api/certificate/generate`

**Descripción:** Genera un certificado PDF con datos proporcionados directamente (no necesita estar en la base de datos).

**Body (JSON):**
```json
{
  "nombre": "URIARTE FERNANDEZ, M PILAR",
  "dni": "30576226A",
  "centro": "CD Zegama",
  "fecha": "2024-12-15"  // Opcional. Si no se proporciona, usa la fecha actual
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://localhost:5000/api/certificate/generate \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "URIARTE FERNANDEZ, M PILAR",
    "dni": "30576226A",
    "centro": "CD Zegama"
  }' \
  --output certificado.pdf
```

**Respuestas:**
- **200 OK**: Descarga el archivo PDF
- **400 Bad Request**: Si faltan datos requeridos (nombre, dni, centro)
- **500 Internal Server Error**: Si hay un error generando el PDF

---

## Características del Certificado

El certificado PDF incluye:

- **Encabezado GSR** con logo y branding verde
- **Nombre y DNI** del participante en destacado
- **Texto de aprobación** en español y euskera
- **Nombre del curso**: "Curso Online GSR Manipulación de Alimentos"
- **Centro** donde se cursó
- **Fecha** de emisión
- **Espacio para firma**
- **Pie de página** con datos de emisión

---

## Ejemplo de Integración en JavaScript

```javascript
// Descargar certificado desde un registro existente
async function descargarCertificado(registroId) {
  try {
    const response = await fetch(`/api/certificate/${registroId}`);
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Certificado_${registroId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } else {
      console.error('Error descargando el certificado');
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

// O generar uno personalizado
async function generarCertificado(nombre, dni, centro) {
  try {
    const response = await fetch('/api/certificate/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ nombre, dni, centro })
    });
    
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Certificado_${nombre.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

## Notas Técnicas

- Los certificados se generan dinámicamente usando **ReportLab**
- El formato del certificado es A4 horizontal (landscape)
- Los certificados NO se guardan en disco, se generan en memoria
- El nombre del archivo descargado incluye el nombre del participante sanitizado
