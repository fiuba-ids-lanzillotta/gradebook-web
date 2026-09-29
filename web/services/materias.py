"""Consumo de gradebook-api para el catálogo de materias."""
import logging

import requests

from web.constants import API_BASE_URL, api_headers
from web.services.respuestas_api import respuesta_no_autorizada

logger = logging.getLogger(__name__)


def listar_materias(token: str) -> list[dict]:
    """GET /materias — catálogo {id, codigo, nombre}. Retorna [] si falla."""
    try:
        response = requests.get(
            f'{API_BASE_URL}/materias',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=10,
        )

        if response.status_code == 200:
            return response.json() or []

        if respuesta_no_autorizada(response):
            return []

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")
    except Exception as error:
        logger.error(f"Error al listar materias: {error}")

    return []
