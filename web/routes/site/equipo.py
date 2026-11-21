"""Pantalla del alumno: su equipo en la evaluación con creación habilitada."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from web.auth_sesion import login_required, redirigir_a_login_sin_sesion
from web.services import grupos as servicio

equipo_bp = Blueprint('equipo', __name__)


def _token() -> str:
    return session.get('token') or ''


def _estado() -> dict:
    resultado = servicio.mi_equipo(_token())

    if resultado.get('unauthorized'):
        return {'unauthorized': True}

    datos = resultado.get('datos') or {}

    return {
        'unauthorized': False,
        'ok': resultado.get('ok'),
        'error': None if resultado.get('ok') else resultado.get('error'),
        'yo': datos.get('yo') or {},
        'evaluacion': datos.get('evaluacion') or {},
        'puede_crear': bool(datos.get('puede_crear')),
        'puede_editar': bool(datos.get('puede_editar')),
        'grupo': datos.get('grupo') or {},
    }


def _nombre(yo: dict) -> str:
    nombre = f"{yo.get('nombre') or ''} {yo.get('apellido') or ''}".strip()

    return nombre or (session.get('usuario') or {}).get('email') or 'Alumno'


@equipo_bp.route('/equipo')
@login_required
def index():
    estado = _estado()

    if estado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return render_template('site/equipo.html', nombre=_nombre(estado['yo']), **estado)


@equipo_bp.route('/equipo', methods=['POST'])
@login_required
def crear():
    padrones = [valor.strip() for valor in request.form.getlist('padron') if valor.strip()]
    resultado = servicio.crear_mi_equipo(_token(), request.form.get('nombre') or '', padrones)

    return _volver(resultado, 'Equipo creado.')


@equipo_bp.route('/equipo/nombre', methods=['POST'])
@login_required
def renombrar():
    resultado = servicio.renombrar_mi_equipo(_token(), request.form.get('nombre') or '')

    return _volver(resultado, 'Nombre actualizado.')


@equipo_bp.route('/equipo/integrantes', methods=['POST'])
@login_required
def agregar():
    resultado = servicio.agregar_padron(_token(), request.form.get('padron') or '')

    return _volver(resultado, 'Integrante agregado.')


@equipo_bp.route('/equipo/salir', methods=['POST'])
@login_required
def salir():
    resultado = servicio.salir_de_mi_equipo(_token())

    return _volver(resultado, 'Saliste del equipo.')


def _volver(resultado: dict, mensaje_ok: str):
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if resultado.get('ok'):
        flash(mensaje_ok, 'ok')
    else:
        flash(resultado.get('error') or 'No se pudo completar.', 'error')

    return redirect(url_for('web.site.equipo.index'))
