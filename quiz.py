"""Lógica de corrección y validación del cuestionario de manipulación de
alimentos."""
from config import CENTROS, REQUIRED_QUESTIONS, VALID_ANSWERS


def calculate_score(respuestas):
    score = 0
    cleaned = {}
    for question, answer in VALID_ANSWERS.items():
        value = str(respuestas.get(question, '')).strip()
        cleaned[question] = value
        if value == answer:
            score += 1
    return score, cleaned


def validate_registro_payload(data):
    nombre = (data.get('nombre') or '').strip()
    dni = (data.get('dni') or '').strip()
    email = (data.get('email') or '').strip()
    centro = (data.get('centro') or '').strip()
    respuestas = data.get('respuestas')

    if not nombre or not dni or not email or not centro:
        return None, None, None, None, None, 'Faltan datos obligatorios: nombre, dni, email y centro son requeridos.'

    if centro not in CENTROS:
        return None, None, None, None, None, 'Centro no válido. Selecciona uno de la lista.'

    if not isinstance(respuestas, dict):
        return None, None, None, None, None, 'El campo respuestas debe ser un objeto con todas las preguntas.'

    missing = [q for q in REQUIRED_QUESTIONS if not str(respuestas.get(q, '')).strip()]
    if missing:
        return None, None, None, None, None, f'Faltan respuestas para las preguntas: {", ".join(missing)}.'

    score, cleaned_respuestas = calculate_score(respuestas)
    return nombre, dni, email, centro, score, cleaned_respuestas
