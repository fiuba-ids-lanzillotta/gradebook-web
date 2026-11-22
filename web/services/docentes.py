"""Consumo de gradebook-api para docentes (identidad del sidebar)."""
from web.services.respuestas_api import pedir_api


def obtener_docente(token: str, docente_id: int) -> dict:
    """GET /docentes/{id} → {'ok', 'datos': docente}."""
    return pedir_api(token, 'GET', f'/docentes/{docente_id}')


def listar_docentes(token: str) -> dict:
    """GET /docentes → {'ok', 'docentes': [...]}."""
    resultado = pedir_api(token, 'GET', '/docentes')

    if not resultado.get('ok'):
        return resultado

    return {'ok': True, 'docentes': resultado.get('datos') or []}


def crear_docente(token: str, nombre: str, apellido: str, email: str, rol: str) -> dict:
    """POST /docentes → {'ok', 'datos': docente creado}."""
    return pedir_api(
        token, 'POST', '/docentes',
        json_body={'nombre': nombre, 'apellido': apellido, 'email': email, 'rol': rol},
        ok=(201,),
    )


def actualizar_docente(token: str, docente_id: int, nombre: str, apellido: str, email: str, rol: str) -> dict:
    """PUT /docentes/{id} → {'ok', 'datos': docente actualizado}."""
    return pedir_api(
        token, 'PUT', f'/docentes/{docente_id}',
        json_body={'nombre': nombre, 'apellido': apellido, 'email': email, 'rol': rol},
        ok=(200,),
    )


def eliminar_docente(token: str, docente_id: int) -> dict:
    """DELETE /docentes/{id} → {'ok'}."""
    return pedir_api(token, 'DELETE', f'/docentes/{docente_id}', ok=(200,))


def actualizar_permisos_docente(token: str, docente_id: int, permisos: list[dict]) -> dict:
    """PUT /docentes/{id}/permisos. Envia overrides [{permiso, concedido}]."""
    return pedir_api(
        token, 'PUT', f'/docentes/{docente_id}/permisos',
        json_body={'permisos': permisos}, ok=(200,),
    )
