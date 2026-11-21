"""Filtro global de cursada: con varias materias vigentes, gana la de la cátedra."""
from flask import session

from app import app as flask_app
from web.cursada_filtro import elegida


def _filas_dos_materias_vigentes():
    return [
        {'id': 8, 'codigo': 'TB099', 'anio': 2027, 'cuatrimestre': 1, 'vigente': True},
        {'id': 3, 'codigo': 'TB022', 'anio': 2026, 'cuatrimestre': 2, 'vigente': True},
    ]


def test_elegida_prefiere_la_vigente_de_la_catedra():
    # Aunque otra materia aparezca primero, la vigente de TB022 es la elegida.
    with flask_app.test_request_context():
        assert elegida('token', _filas_dos_materias_vigentes())['id'] == 3


def test_elegida_sin_vigente_de_catedra_cae_a_la_primera_vigente():
    filas = [
        {'id': 3, 'codigo': 'TB022', 'anio': 2026, 'cuatrimestre': 1, 'vigente': False},
        {'id': 8, 'codigo': 'TB099', 'anio': 2027, 'cuatrimestre': 1, 'vigente': True},
    ]

    with flask_app.test_request_context():
        assert elegida('token', filas)['id'] == 8


def test_elegida_respeta_la_seleccion_manual_de_sesion():
    # La elegida a mano en el filtro gana, aunque sea de otra materia.
    with flask_app.test_request_context():
        session['cursada_id'] = 8

        assert elegida('token', _filas_dos_materias_vigentes())['id'] == 8
