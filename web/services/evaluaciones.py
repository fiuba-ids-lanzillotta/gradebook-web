"""Consumo de gradebook-api para las categorías de una cursada."""
import logging

import requests

from web.constants import API_BASE_URL, api_headers
from web.services.respuestas_api import mensaje_error_api, respuesta_no_autorizada

logger = logging.getLogger(__name__)


def listar(token: str, cursada_id: int) -> dict:
    return _pedir(token, 'GET', f'/cursadas/{cursada_id}/evaluaciones', ok=(200,))


def crear(token: str, cursada_id: int, datos: dict) -> dict:
    return _pedir(token, 'POST', f'/cursadas/{cursada_id}/evaluaciones', json_body=datos, ok=(201,))


def habilitar_grupos(token: str, evaluacion_id: int, habilitado: bool) -> dict:
    return _pedir(
        token, 'PUT', f'/evaluaciones/{evaluacion_id}/crear-grupos',
        json_body={'habilitado': habilitado}, ok=(200,),
    )


def _pedir(token: str, method: str, path: str, *, json_body=None, ok=(200,)) -> dict:
    try:
        response = requests.request(
            method,
            f'{API_BASE_URL}{path}',
            json=json_body,
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}
    except Exception as error:
        logger.error(f"Error en {method} {path}: {error}")

        return {'ok': False, 'error': 'Ocurrió un error al hablar con el servidor.'}

    no_autorizada = respuesta_no_autorizada(response)

    if no_autorizada:
        return no_autorizada

    if response.status_code not in ok:
        return {'ok': False, 'error': mensaje_error_api(response), 'status': response.status_code}

    try:
        datos = response.json() or {}
    except Exception:
        datos = {}

    return {'ok': True, 'datos': datos}
