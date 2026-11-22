"""Helpers compartidos para hablar con la API (gradebook-api)."""
import logging

import requests

from web.constants import API_BASE_URL, api_headers

logger = logging.getLogger(__name__)

_MENSAJE_SESION_EXPIRADA = 'Sesión expirada. Volvé a iniciar sesión.'


def pedir_api(token: str, method: str, path: str, *, json_body=None, params=None,
              ok=(200,), timeout=15) -> dict:
    """Request autenticada a gradebook-api.

    Devuelve `{'ok': True, 'datos': {...}}` (con `'vacio': True` si la API
    respondió 204), `{'ok': False, 'error': ..., 'status': ...}` ante error, o
    `{'ok': False, 'unauthorized': True, ...}` ante 401/403.
    """
    try:
        response = requests.request(
            method,
            f'{API_BASE_URL}{path}',
            json=json_body,
            params=params,
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=timeout,
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

    if response.status_code == 204:
        return {'ok': True, 'vacio': True, 'datos': {}}

    if response.status_code not in ok:
        return {
            'ok': False,
            'error': mensaje_error_api(response),
            'status': response.status_code,
        }

    try:
        datos = response.json() or {}
    except Exception:
        datos = {}

    return {'ok': True, 'datos': datos}


def mensaje_error_api(response) -> str:
    """Extrae un mensaje legible del cuerpo de error de la API, o uno genérico."""
    try:
        datos = response.json()
        errores = datos.get('errors') or []

        if errores:
            textos = [
                error.get('description') or error.get('message') or ''
                for error in errores
            ]

            return ' '.join(texto for texto in textos if texto) or 'Error de validación.'
    except Exception:
        pass

    return f'Error del servidor (HTTP {response.status_code}).'


def respuesta_no_autorizada(response) -> dict | None:
    """Si la API respondió 401/403, arma el resultado de sesión expirada; si no, None."""
    if response.status_code in (401, 403):
        return {'ok': False, 'error': _MENSAJE_SESION_EXPIRADA, 'unauthorized': True}

    return None
