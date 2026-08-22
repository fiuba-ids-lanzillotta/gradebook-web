"""Consumo de gradebook-api para docentes (identidad del sidebar)."""
import logging
import requests

from web.constants import API_BASE_URL, api_headers
from web.services.respuestas_api import respuesta_no_autorizada

logger = logging.getLogger(__name__)


def obtener_docente(token: str, docente_id: int) -> dict:
    """GET /docentes/{id}. Retorna el dict o {} si falla."""
    try:
        response = requests.get(
            f'{API_BASE_URL}/docentes/{docente_id}',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=10,
        )

        if response.status_code == 200:
            return response.json() or {}

        no_autorizada = respuesta_no_autorizada(response)
        if no_autorizada:
            return {'_unauthorized': True}

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")
    except Exception as error:
        logger.error(f"Error al obtener docente {docente_id}: {error}")

    return {}