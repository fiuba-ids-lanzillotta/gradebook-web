"""Cursada elegida en el panel. Filtro global, guardado en la sesión."""
from flask import g, session

from web.constants import MATERIA_CODIGO
from web.services.cursos import listar_cursadas, obtener_cursada_vigente

CLAVE = 'cursada_id'


def opciones(token: str) -> list[dict]:
    """Historial de cursadas del docente. Vacío si no hay token o la API falla."""
    if not token:
        return []

    cache = getattr(g, '_cursadas_opciones', None)

    if cache is not None and cache[0] == token:
        return cache[1]

    resultado = listar_cursadas(token)
    filas = (resultado.get('cursadas') or []) if resultado.get('ok') else []
    g._cursadas_opciones = (token, filas)

    return filas


def elegida(token: str, cursadas: list[dict] | None = None) -> dict:
    """
    La cursada del filtro, o la vigente, o la primera del historial.
    Con varias materias vigentes, gana la de la cátedra (MATERIA_CODIGO).
    """
    filas = opciones(token) if cursadas is None else cursadas
    buscada = session.get(CLAVE)
    coincidente = _por_id(filas, buscada)

    if coincidente:
        return coincidente

    preferida = _vigente(filas, MATERIA_CODIGO) or _vigente(filas) or (filas[0] if filas else {})

    if preferida:
        session[CLAVE] = preferida.get('id')

        return preferida

    return obtener_cursada_vigente(token) if token else {}


def guardar(cursada_id) -> None:
    session[CLAVE] = cursada_id


def _vigente(filas: list[dict], codigo=None) -> dict:
    """La primera cursada vigente de `codigo` (o de cualquier materia si es None)."""
    for fila in filas:
        if fila.get('vigente') and (codigo is None or fila.get('codigo') == codigo):
            return fila

    return {}


def _por_id(filas: list[dict], cursada_id) -> dict:
    if cursada_id is None or str(cursada_id).strip() == '':
        return {}

    for fila in filas:
        if str(fila.get('id')) == str(cursada_id):
            return fila

    return {}
