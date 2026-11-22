"""Consumo de gradebook-api para las cursadas (cursos)."""
import logging

import requests

from web.constants import API_BASE_URL, MATERIA_CODIGO, api_headers
from web.services.respuestas_api import pedir_api

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
    resultado = pedir_api(
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
    return pedir_api(token, 'POST', '/cursadas', json_body=_body_cursada(datos), ok=(201,))


def actualizar_cursada(token: str, cursada_id: int, datos: dict) -> dict:
    """PUT /cursadas/{id}. El codigo debe coincidir con la materia actual."""
    return pedir_api(token, 'PUT', f'/cursadas/{cursada_id}', json_body=_body_cursada(datos), ok=(200,))


def _body_cursada(datos: dict) -> dict:
    return {
        'codigo': (datos.get('codigo') or '').strip().upper(),
        'nombre': (datos.get('nombre') or '').strip(),
        'anio': _anio_cursada(datos),
        'cuatrimestre': _entero(datos.get('cuatrimestre')),
        'fecha_inicio': (datos.get('fecha_inicio') or '').strip(),
        'fecha_fin': (datos.get('fecha_fin') or '').strip(),
    }


def _anio_cursada(datos: dict):
    """Año explícito, o el de las fechas si inicio y fin caen en el mismo año."""
    explicito = str(datos.get('anio') or '').strip()

    if explicito:
        return _entero(explicito)

    inicio = (datos.get('fecha_inicio') or '').strip()
    fin = (datos.get('fecha_fin') or '').strip()
    anio_inicio = inicio[:4]
    anio_fin = fin[:4]

    if len(anio_inicio) == 4 and anio_inicio.isdigit() and anio_inicio == anio_fin:
        return int(anio_inicio)

    return None


def _entero(valor):
    try:
        return int(str(valor or '').strip())
    except (TypeError, ValueError):
        return valor
