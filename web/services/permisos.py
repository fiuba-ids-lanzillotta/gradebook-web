"""Consumo de gradebook-api para permisos (catálogo)."""
from web.services.respuestas_api import pedir_api


def obtener_catalogo_permisos(token: str) -> list[dict]:
    """GET /permisos. Retorna el catálogo de permisos o [] si falla."""
    resultado = pedir_api(token, 'GET', '/permisos')

    if not resultado.get('ok'):
        return []

    return resultado.get('datos') or []
