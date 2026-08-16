import requests
import pytest

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True

    return flask_app.test_client()


# --- páginas públicas (services vía requests, mockeado) ---

def test_pagina_inicio_ok(client):
    respuesta = client.get('/')

    assert respuesta.status_code == 200


def test_pagina_items_ok(client, monkeypatch, respuesta_falsa, cargar_json):
    lista = cargar_json('json/items/lista.json')
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: respuesta_falsa(200, lista))

    respuesta = client.get('/items')

    assert respuesta.status_code == 200


def test_pagina_items_degrada_si_api_cae(client, monkeypatch):
    def _sin_conexion(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, 'get', _sin_conexion)

    respuesta = client.get('/items')

    assert respuesta.status_code == 200


def test_pagina_inexistente_devuelve_404(client):
    respuesta = client.get('/no-existe')

    assert respuesta.status_code == 404


# --- admin (protegido por admin_required) ---

def test_admin_panel_requiere_login(client):
    respuesta = client.get('/admin/')

    assert respuesta.status_code == 302
    assert '/admin/login' in respuesta.headers['Location']


def test_admin_items_requiere_login(client):
    respuesta = client.get('/admin/items')

    assert respuesta.status_code == 302
    assert '/admin/login' in respuesta.headers['Location']


def test_login_exitoso_redirige_al_panel(client, monkeypatch, respuesta_falsa, cargar_json):
    cuerpo = cargar_json('json/auth/login.json')
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(200, cuerpo))

    respuesta = client.post('/admin/login', data={'usuario': 'admin', 'password': 'secreto'})

    assert respuesta.status_code == 302
    assert respuesta.headers['Location'].endswith('/admin/')


def test_login_fallido_muestra_pagina(client, monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(401))

    respuesta = client.post('/admin/login', data={'usuario': 'admin', 'password': 'mala'})

    assert respuesta.status_code == 200
