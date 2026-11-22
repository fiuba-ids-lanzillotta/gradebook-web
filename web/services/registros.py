"""Consumo de gradebook-api para el registro de auditoría."""
from web.services.respuestas_api import pedir_api


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

    return pedir_api(token, 'GET', '/registros', params=consulta, ok=(200, 204))
