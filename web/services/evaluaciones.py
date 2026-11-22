"""Consumo de gradebook-api para las categorías de una cursada."""
from web.services.respuestas_api import pedir_api


def listar(token: str, cursada_id: int) -> dict:
    return pedir_api(token, 'GET', f'/cursadas/{cursada_id}/evaluaciones', ok=(200,))


def crear(token: str, cursada_id: int, datos: dict) -> dict:
    return pedir_api(token, 'POST', f'/cursadas/{cursada_id}/evaluaciones', json_body=datos, ok=(201,))


def habilitar_grupos(token: str, evaluacion_id: int, habilitado: bool) -> dict:
    return pedir_api(
        token, 'PUT', f'/evaluaciones/{evaluacion_id}/crear-grupos',
        json_body={'habilitado': habilitado}, ok=(200,),
    )
