"""Consumo de gradebook-api para el registro de auditoría."""
import logging

import requests

from web.constants import API_BASE_URL, api_headers
from web.services.respuestas_api import mensaje_error_api, respuesta_no_autorizada

logger = logging.getLogger(__name__)


def listar(token: str, email: str = '', accion: str = '', tipo: str = '',
           orden: str = 'desc', offset: int = 0, limit: int = 20) -> dict:
    params = {
        'email': email or None,
        'accion': accion or None,
        'tipo': tipo or None,
        '_orden': orden or 'desc',
        '_offset': offset,
        '_limit': limit,
    }
    consulta = {clave: valor for clave, valor in params.items() if valor not in (None, '')}

    return _pedir(token, 'GET', '/registros', params=consulta, ok=(200, 204))


def _pedir(token: str, method: str, path: str, *, params=None, ok=(200,)) -> dict:
    try:
        response = requests.request(
            method,
            f'{API_BASE_URL}{path}',
            params=params,
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

    if response.status_code == 204 or not response.content:
        return {'ok': True, 'datos': {'registros': [], '_links': {}}}

    try:
        datos = response.json() or {}
    except Exception:
        datos = {}

    return {'ok': True, 'datos': datos}
