"""Consumo de gradebook-api para las cursadas (cursos)."""
import logging

import requests

from web.constants import API_BASE_URL, MATERIA_CODIGO, api_headers
from web.services.respuestas_api import mensaje_error_api, respuesta_no_autorizada

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


def listar_cursadas(token: str) -> dict:
    """GET /cursadas — historial de cursadas (pocas por materia: un pedido alcanza)."""
    resultado = _pedir(
        token,
        'GET',
        '/cursadas',
        params={'_offset': 0, '_limit': 100},
        ok=(200, 204),
    )

    if not resultado.get('ok'):
        return resultado

    if resultado.get('vacio'):
        return {'ok': True, 'cursadas': []}

    return {'ok': True, 'cursadas': (resultado.get('datos') or {}).get('cursadas') or []}


def crear_cursada(token: str, datos: dict) -> dict:
    """POST /cursadas. Si la materia no existe, la API la crea."""
    return _pedir(token, 'POST', '/cursadas', json_body=_body_cursada(datos), ok=(201,))


def actualizar_cursada(token: str, cursada_id: int, datos: dict) -> dict:
    """PUT /cursadas/{id}. El codigo debe coincidir con la materia actual."""
    return _pedir(token, 'PUT', f'/cursadas/{cursada_id}', json_body=_body_cursada(datos), ok=(200,))


def _body_cursada(datos: dict) -> dict:
    return {
        'codigo': (datos.get('codigo') or '').strip().upper(),
        'nombre': (datos.get('nombre') or '').strip(),
        'anio': _entero(datos.get('anio')),
        'cuatrimestre': _entero(datos.get('cuatrimestre')),
        'fecha_inicio': (datos.get('fecha_inicio') or '').strip(),
        'fecha_fin': (datos.get('fecha_fin') or '').strip(),
    }


def _entero(valor):
    try:
        return int(str(valor or '').strip())
    except (TypeError, ValueError):
        return valor


def _pedir(token: str, method: str, path: str, *, json_body=None, params=None, ok=(200,), timeout=15) -> dict:
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
