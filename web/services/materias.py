"""Consumo de gradebook-api para el catálogo de materias."""
from web.services.respuestas_api import pedir_api


def listar_materias(token: str) -> list[dict]:
    """GET /materias — catálogo {id, codigo, nombre}. Retorna [] si falla."""
    resultado = pedir_api(token, 'GET', '/materias')

    if not resultado.get('ok'):
        return []

    return resultado.get('datos') or []
