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
