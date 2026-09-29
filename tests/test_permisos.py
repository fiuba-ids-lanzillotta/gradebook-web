import requests

from web.services import permisos


def test_catalogo_devuelve_permisos(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(200, [{'codigo': 'x.leer'}]))

    assert permisos.obtener_catalogo_permisos('token') == [{'codigo': 'x.leer'}]


def test_catalogo_sin_autorizacion_devuelve_vacio(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(403))

    assert permisos.obtener_catalogo_permisos('token') == []


def test_catalogo_sin_conexion_devuelve_vacio(monkeypatch):
    def _sin_conexion(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, 'get', _sin_conexion)

    assert permisos.obtener_catalogo_permisos('token') == []
