import requests

from web.services import cursos


def test_obtener_cursada_vigente_devuelve_la_vigente(monkeypatch, respuesta_falsa):
    cuerpo = {'cursadas': [
        {'codigo': 'TB022', 'anio': 2025, 'cuatrimestre': 1, 'vigente': False},
        {'codigo': 'TB022', 'anio': 2026, 'cuatrimestre': 2, 'vigente': True},
    ], '_links': {}}
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(200, cuerpo))

    assert cursos.obtener_cursada_vigente('token') == {
        'codigo': 'TB022', 'anio': 2026, 'cuatrimestre': 2, 'vigente': True,
    }


def test_obtener_cursada_vigente_ninguna(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(200, {'cursadas': [{'vigente': False}]}))

    assert cursos.obtener_cursada_vigente('token') == {}


def test_obtener_cursada_vigente_error(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(403))

    assert cursos.obtener_cursada_vigente('token') == {}


# --- listado / alta / edición (pantalla Cursada) ---

def test_listar_cursadas_devuelve_historial(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(method, url, params=None, **kwargs):
        capturado['url'] = url
        capturado['params'] = params
        return respuesta_falsa(200, {'cursadas': [{'id': 1, 'codigo': 'TB022'}]})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = cursos.listar_cursadas('token')

    assert capturado['url'].endswith('/cursadas')
    assert resultado['ok'] and resultado['cursadas'][0]['id'] == 1


def test_listar_cursadas_204_devuelve_vacio(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(204))

    assert cursos.listar_cursadas('token') == {'ok': True, 'cursadas': []}


def test_crear_cursada_postea_body_normalizado(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(method, url, json=None, **kwargs):
        capturado['method'] = method
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(201, {'id': 9})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = cursos.crear_cursada('token', {
        'codigo': 'tb022', 'nombre': 'IDS', 'anio': '2027', 'cuatrimestre': '1',
        'fecha_inicio': '2027-03-01', 'fecha_fin': '2027-07-15',
    })

    assert capturado['method'] == 'POST'
    assert capturado['url'].endswith('/cursadas')
    assert capturado['json'] == {
        'codigo': 'TB022', 'nombre': 'IDS', 'anio': 2027, 'cuatrimestre': 1,
        'fecha_inicio': '2027-03-01', 'fecha_fin': '2027-07-15',
    }
    assert resultado['ok']


def test_actualizar_cursada_putea_body(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(method, url, json=None, **kwargs):
        capturado['method'] = method
        capturado['url'] = url
        return respuesta_falsa(200, {'id': 9})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = cursos.actualizar_cursada('token', 9, {
        'codigo': 'TB022', 'nombre': 'IDS', 'anio': '2026', 'cuatrimestre': '2',
        'fecha_inicio': '2026-08-01', 'fecha_fin': '2026-12-10',
    })

    assert capturado['method'] == 'PUT'
    assert capturado['url'].endswith('/cursadas/9')
    assert resultado['ok']


def test_crear_cursada_error_devuelve_mensaje(monkeypatch, respuesta_falsa):
    cuerpo = {'errors': [{'code': 'x', 'description': 'fechas fuera del cuatrimestre'}]}
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(400, cuerpo))

    resultado = cursos.crear_cursada('token', {})

    assert resultado['ok'] is False
    assert 'cuatrimestre' in resultado['error']


def test_listar_cursadas_401_devuelve_unauthorized(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(401))

    resultado = cursos.listar_cursadas('token')

    assert resultado['ok'] is False
    assert resultado['unauthorized'] is True
