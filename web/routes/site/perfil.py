"""Pantalla del alumno: su perfil de notas, igual al del docente y sin edición."""
from flask import Blueprint, render_template, session

from web.auth_sesion import login_required, redirigir_a_login_sin_sesion
from web.notas_vista import preparar_categorias
from web.services import notas as servicio

perfil_bp = Blueprint('perfil', __name__)


@perfil_bp.route('/perfil')
@login_required
def index():
    resultado = servicio.mias(session.get('token') or '')

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    datos = resultado.get('datos') or {}
    estudiante = datos.get('estudiante') or {}
    nombre = f"{estudiante.get('nombre') or ''} {estudiante.get('apellido') or ''}".strip()
    nombre = nombre or (session.get('usuario') or {}).get('email') or 'Alumno'

    return render_template(
        'site/perfil.html',
        nombre=nombre,
        estudiante=estudiante,
        categorias=preparar_categorias(datos.get('categorias') or [], False),
        puede_editar=False,
        error=None if resultado.get('ok') else resultado.get('error'),
    )
