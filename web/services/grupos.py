"""Consumo de gradebook-api para los equipos de una cursada."""
import logging

import requests

from web.constants import API_BASE_URL, api_headers
from web.services.respuestas_api import mensaje_error_api, respuesta_no_autorizada

logger = logging.getLogger(__name__)


def mi_equipo(token: str) -> dict:
    return _pedir(token, 'GET', '/me/equipo', ok=(200,))


def crear_mi_equipo(token: str, nombre: str, padrones: list[str]) -> dict:
    return _pedir(
        token, 'POST', '/me/equipo',
        json_body={'nombre': nombre, 'padrones': padrones}, ok=(201,),
    )


def renombrar_mi_equipo(token: str, nombre: str) -> dict:
    return _pedir(token, 'PUT', '/me/equipo', json_body={'nombre': nombre}, ok=(200,))


def agregar_padron(token: str, padron: str) -> dict:
    return _pedir(token, 'POST', '/me/equipo/integrantes', json_body={'padron': padron}, ok=(201,))


def salir_de_mi_equipo(token: str) -> dict:
    return _pedir(token, 'POST', '/me/equipo/salir', ok=(200,))


def listar(token: str, cursada_id: int) -> dict:
    return _pedir(token, 'GET', f'/cursadas/{cursada_id}/grupos', ok=(200,))


def obtener(token: str, grupo_id: int) -> dict:
    return _pedir(token, 'GET', f'/grupos/{grupo_id}', ok=(200,))


def guardar_tutores(token: str, asignaciones: list[dict]) -> dict:
    return _pedir(token, 'PUT', '/grupos/tutores', json_body={'asignaciones': asignaciones}, ok=(200,))


def renombrar(token: str, grupo_id: int, nombre: str) -> dict:
    return _pedir(token, 'PUT', f'/grupos/{grupo_id}', json_body={'nombre': nombre}, ok=(200,))


def agregar_integrante(token: str, grupo_id: int, estudiante_id: int) -> dict:
    return _pedir(
        token, 'POST', f'/grupos/{grupo_id}/integrantes',
        json_body={'estudiante_id': estudiante_id}, ok=(201,),
    )


def echar_integrante(token: str, grupo_id: int, estudiante_id: int) -> dict:
    return _pedir(token, 'DELETE', f'/grupos/{grupo_id}/integrantes/{estudiante_id}', ok=(200,))


def transferir_integrante(token: str, grupo_id: int, estudiante_id: int, grupo_destino_id: int) -> dict:
    return _pedir(
        token, 'POST', f'/grupos/{grupo_id}/integrantes/{estudiante_id}/transferir',
        json_body={'grupo_destino_id': grupo_destino_id}, ok=(200,),
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
