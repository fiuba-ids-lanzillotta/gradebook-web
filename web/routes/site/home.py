from flask import Blueprint, render_template, session

from web.auth_sesion import login_required, redirigir_a_login_sin_sesion
from web.services import grupos as servicio

home_bp = Blueprint('home', __name__)


def _nombre(yo: dict) -> str:
    nombre = f"{yo.get('nombre') or ''} {yo.get('apellido') or ''}".strip()

    return nombre or (session.get('usuario') or {}).get('email') or 'Alumno'


@home_bp.route('/')
@login_required
def index():
    resultado = servicio.mi_equipo(session.get('token') or '')

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    yo = (resultado.get('datos') or {}).get('yo') or {}

    return render_template('site/inicio.html', nombre=_nombre(yo))