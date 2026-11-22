"""Consumo de gradebook-api para los equipos de una cursada."""
from web.services.respuestas_api import pedir_api


def mi_equipo(token: str) -> dict:
    return pedir_api(token, 'GET', '/me/equipo', ok=(200,))


def crear_mi_equipo(token: str, nombre: str, padrones: list[str]) -> dict:
    return pedir_api(
        token, 'POST', '/me/equipo',
        json_body={'nombre': nombre, 'padrones': padrones}, ok=(201,),
    )


def renombrar_mi_equipo(token: str, nombre: str) -> dict:
    return pedir_api(token, 'PUT', '/me/equipo', json_body={'nombre': nombre}, ok=(200,))


def agregar_padron(token: str, padron: str) -> dict:
    return pedir_api(token, 'POST', '/me/equipo/integrantes', json_body={'padron': padron}, ok=(201,))


def salir_de_mi_equipo(token: str) -> dict:
    return pedir_api(token, 'POST', '/me/equipo/salir', ok=(200,))


def listar(token: str, cursada_id: int) -> dict:
    return pedir_api(token, 'GET', f'/cursadas/{cursada_id}/grupos', ok=(200,))


def obtener(token: str, grupo_id: int) -> dict:
    return pedir_api(token, 'GET', f'/grupos/{grupo_id}', ok=(200,))


def guardar_tutores(token: str, asignaciones: list[dict]) -> dict:
    return pedir_api(token, 'PUT', '/grupos/tutores', json_body={'asignaciones': asignaciones}, ok=(200,))


def renombrar(token: str, grupo_id: int, nombre: str) -> dict:
    return pedir_api(token, 'PUT', f'/grupos/{grupo_id}', json_body={'nombre': nombre}, ok=(200,))


def agregar_integrante(token: str, grupo_id: int, estudiante_id: int) -> dict:
    return pedir_api(
        token, 'POST', f'/grupos/{grupo_id}/integrantes',
        json_body={'estudiante_id': estudiante_id}, ok=(201,),
    )


def echar_integrante(token: str, grupo_id: int, estudiante_id: int) -> dict:
    return pedir_api(token, 'DELETE', f'/grupos/{grupo_id}/integrantes/{estudiante_id}', ok=(200,))


def transferir_integrante(token: str, grupo_id: int, estudiante_id: int, grupo_destino_id: int) -> dict:
    return pedir_api(
        token, 'POST', f'/grupos/{grupo_id}/integrantes/{estudiante_id}/transferir',
        json_body={'grupo_destino_id': grupo_destino_id}, ok=(200,),
    )
