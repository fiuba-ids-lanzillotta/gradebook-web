"""Consumo de gradebook-api para las calificaciones de un alumno."""
from web.services.respuestas_api import pedir_api


def calificaciones(token: str, cursada_id: int, estudiante_id: int) -> dict:
    return pedir_api(
        token, 'GET', f'/cursadas/{cursada_id}/estudiantes/{estudiante_id}/calificaciones', ok=(200,),
    )


def cargar(token: str, instancia_id: int, notas: list) -> dict:
    return pedir_api(
        token, 'PUT', f'/instancias/{instancia_id}/notas',
        json_body={'notas': notas}, ok=(200,),
    )
