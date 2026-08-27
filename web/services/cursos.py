"""Consumo de gradebook-api para las cursadas (cursos)."""
import logging

import requests

from web.constants import API_BASE_URL, MATERIA_CODIGO, api_headers

logger = logging.getLogger(__name__)


def obtener_cursada_vigente(token: str) -> dict:
    """Devuelve la cursada vigente de la materia (código MATERIA_CODIGO), o {}.

    Consulta GET /cursadas?codigo=MATERIA_CODIGO y toma la primera con vigente=true.
    Ante error/no autorizado/sin resultados, retorna {} (el llamador usa el respaldo).
    """
    try:
        response = requests.get(
            f'{API_BASE_URL}/cursadas',
            params={'codigo': MATERIA_CODIGO, '_limit': 100},
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {}
    except Exception as error:
        logger.error(f"Error al obtener cursadas: {error}")
        
        return {}

    if response.status_code != 200:
        return {}

    cursos = (response.json() or {}).get('cursadas') or []

    for curso in cursos:
        if curso.get('vigente'):
            return curso

    return {}
