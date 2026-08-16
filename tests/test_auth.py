import requests

from web.services import auth


def test_autenticar_ok(monkeypatch, respuesta_falsa, cargar_json):
    cuerpo = cargar_json('json/auth/login.json')
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(200, cuerpo))

    resultado = auth.autenticar('admin', 'secreto')

    assert resultado == {'ok': True, 'token': cuerpo['token'], 'usuario': cuerpo['usuario']}


def test_autenticar_credenciales_invalidas(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(401))

    resultado = auth.autenticar('admin', 'mala')

    assert resultado['ok'] is False
    assert 'incorrect' in resultado['error'].lower()


def test_autenticar_sin_conexion(monkeypatch):
    def _sin_conexion(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, 'post', _sin_conexion)

    resultado = auth.autenticar('admin', 'secreto')

    assert resultado['ok'] is False


def test_autenticar_error_servidor(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(500))

    resultado = auth.autenticar('admin', 'secreto')

    assert resultado['ok'] is False and '500' in resultado['error']
