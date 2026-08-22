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


# --- recuperación de contraseña ---

def test_solicitar_recuperacion_ok(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(200, {'mensaje': 'ok'}))

    assert auth.solicitar_recuperacion('a@fi.uba.ar') == {'ok': True}


def test_solicitar_recuperacion_sin_conexion(monkeypatch):
    def _sin_conexion(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, 'post', _sin_conexion)

    resultado = auth.solicitar_recuperacion('a@fi.uba.ar')

    assert resultado['ok'] is False


def test_confirmar_recuperacion_ok(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(200, {'mensaje': 'ok'}))

    assert auth.confirmar_recuperacion('token', 'nuevaClave1') == {'ok': True}


def test_confirmar_recuperacion_token_invalido(monkeypatch, respuesta_falsa):
    cuerpo = {'errors': [{'code': 'reset.token.invalido'}]}
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(400, cuerpo))

    resultado = auth.confirmar_recuperacion('malo', 'nuevaClave1')

    assert resultado['ok'] is False and 'enlace' in resultado['error'].lower()
