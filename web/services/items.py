"""Consumo de la API (gradebook-api) para el recurso de ejemplo `items`.

Cada item tiene la forma {id, nombre, descripcion, activo}. Las lecturas
públicas degradan con gracia (devuelven [] si la API no responde); las
escrituras requieren el JWT de admin y devuelven {'ok': ...}.
"""
import logging
import requests

from web.constants import API_BASE_URL, api_headers
from web.services.respuestas_api import mensaje_error_api, respuesta_no_autorizada

logger = logging.getLogger(__name__)


def obtener_items() -> list[dict]:
    """Lista los items públicos. Devuelve [] si la API no responde."""
    try:
        response = requests.get(f'{API_BASE_URL}/items', headers=api_headers(), timeout=10)

        if response.status_code == 200:
            return response.json() or []

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")
    except Exception as error:
        logger.error(f"Error al obtener items: {error}")

    return []


def body_desde_formulario(form) -> dict:
    """Arma el JSON de la API a partir del formulario de item.

    `activo` es un checkbox: presente => True, ausente => False.
    `descripcion` vacía se envía como None (campo opcional en la API).
    """
    return {
        'nombre': (form.get('nombre') or '').strip(),
        'descripcion': (form.get('descripcion') or '').strip() or None,
        'activo': form.get('activo') is not None,
    }


def crear_item(token: str, datos: dict) -> dict:
    """Crea un item vía POST /items (requiere JWT admin)."""
    try:
        response = requests.post(
            f'{API_BASE_URL}/items',
            json=datos,
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=15,
        )

        if response.status_code == 201:
            return {'ok': True}

        no_autorizada = respuesta_no_autorizada(response)

        if no_autorizada:
            return no_autorizada

        return {'ok': False, 'error': mensaje_error_api(response)}

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}

    except Exception as error:
        logger.error(f"Error al crear item: {error}")

        return {'ok': False, 'error': 'Ocurrió un error al agregar el item.'}


def actualizar_item(token: str, item_id: int, datos: dict) -> dict:
    """Actualiza un item vía PUT /items/<id>."""
    try:
        response = requests.put(
            f'{API_BASE_URL}/items/{item_id}',
            json=datos,
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=15,
        )

        if response.status_code == 200:
            return {'ok': True}

        no_autorizada = respuesta_no_autorizada(response)

        if no_autorizada:
            return no_autorizada

        return {'ok': False, 'error': mensaje_error_api(response)}

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}

    except Exception as error:
        logger.error(f"Error al actualizar item: {error}")

        return {'ok': False, 'error': 'Ocurrió un error al guardar el item.'}


def eliminar_item(token: str, item_id: int) -> dict:
    """Elimina un item vía DELETE /items/<id>."""
    try:
        response = requests.delete(
            f'{API_BASE_URL}/items/{item_id}',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=10,
        )

        if response.status_code == 204:
            return {'ok': True}

        no_autorizada = respuesta_no_autorizada(response)

        if no_autorizada:
            return no_autorizada

        return {'ok': False, 'error': mensaje_error_api(response)}

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}

    except Exception as error:
        logger.error(f"Error al eliminar item: {error}")

        return {'ok': False, 'error': 'Ocurrió un error al eliminar el item.'}
