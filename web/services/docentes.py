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


def listar_docentes(token: str) -> list[dict]:
    """GET /docentes. Retorna la lista o [] si falla."""
    try:
        response = requests.get(
            f'{API_BASE_URL}/docentes',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=10,
        )

        if response.status_code == 200:
            return response.json() or []

        no_autorizada = respuesta_no_autorizada(response)
        if no_autorizada:
            return []

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")
    except Exception as error:
        logger.error(f"Error al listar docentes: {error}")

    return []


def crear_docente(token: str, nombre: str, apellido: str, email: str, rol: str) -> dict | None:
    """POST /docentes. Retorna el dict creado o None si falla."""
    try:
        response = requests.post(
            f'{API_BASE_URL}/docentes',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            json={'nombre': nombre, 'apellido': apellido, 'email': email, 'rol': rol},
            timeout=10,
        )

        if response.status_code == 201:
            return response.json()

        no_autorizada = respuesta_no_autorizada(response)

        if no_autorizada:
            return None

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")
    except Exception as error:
        logger.error(f"Error al crear docente: {error}")

    return None


def actualizar_docente(token: str, docente_id: int, nombre: str, apellido: str, email: str, rol: str) -> dict | None:
    """PUT /docentes/{id}. Retorna el dict actualizado o None si falla."""
    try:
        response = requests.put(
            f'{API_BASE_URL}/docentes/{docente_id}',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            json={'nombre': nombre, 'apellido': apellido, 'email': email, 'rol': rol},
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()

        no_autorizada = respuesta_no_autorizada(response)

        if no_autorizada:
            return None

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")
    except Exception as error:
        logger.error(f"Error al actualizar docente {docente_id}: {error}")

    return None


def eliminar_docente(token: str, docente_id: int) -> bool:
    """DELETE /docentes/{id}. Retorna True si fue exitoso."""
    try:
        response = requests.delete(
            f'{API_BASE_URL}/docentes/{docente_id}',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=10,
        )

        if response.status_code == 200:
            return True

        no_autorizada = respuesta_no_autorizada(response)

        if no_autorizada:
            return False

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

    except Exception as error:
        logger.error(f"Error al eliminar docente {docente_id}: {error}")

    return False


def actualizar_permisos_docente(token: str, docente_id: int, permisos: list[dict]) -> bool:
    """PUT /docentes/{id}/permisos. Envia overrides [{permiso, concedido}]."""
    try:
        response = requests.put(
            f'{API_BASE_URL}/docentes/{docente_id}/permisos',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            json={'permisos': permisos},
            timeout=10,
        )

        if response.status_code == 200:
            return True

        no_autorizada = respuesta_no_autorizada(response)

        if no_autorizada:
            return False

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")
        
    except Exception as error:
        logger.error(f"Error al actualizar permisos del docente {docente_id}: {error}")

    return False