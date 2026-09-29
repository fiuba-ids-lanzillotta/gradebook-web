"""Tests para services/materias.py — catálogo de materias (GET /materias)."""
import requests

from web.services import materias


def test_listar_materias_devuelve_catalogo(monkeypatch, respuesta_falsa):
    cuerpo = [
        {'id': 1, 'codigo': 'TB022', 'nombre': 'Introducción al Desarrollo de Software'},
        {'id': 2, 'codigo': 'TB023', 'nombre': 'Otra'},
    ]
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(200, cuerpo))

    assert [m['codigo'] for m in materias.listar_materias('token')] == ['TB022', 'TB023']


def test_listar_materias_vacio(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(200, []))

    assert materias.listar_materias('token') == []


def test_listar_materias_error_500(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(500))

    assert materias.listar_materias('token') == []


def test_listar_materias_sin_conexion(monkeypatch):
    def sin_conexion(*args, **kwargs):
        raise requests.exceptions.ConnectionError('refused')

    monkeypatch.setattr(requests, 'get', sin_conexion)

    assert materias.listar_materias('token') == []


def test_listar_materias_no_autorizada(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(403))

    assert materias.listar_materias('token') == []
