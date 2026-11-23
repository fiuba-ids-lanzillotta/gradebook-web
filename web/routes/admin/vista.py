"""Pantalla admin: planilla de la cursada elegida."""
from flask import Blueprint, render_template

from web.auth_sesion import admin_required, exige_permiso, redirigir_a_login_sin_sesion
from web.constants import PERMISO_NOTAS_LEER
from web.cursada_filtro import elegida
from web.notas_vista import valor_celda
from web.routes.admin.panel import _token, contexto_admin
from web.services import notas as servicio

vista_bp = Blueprint('vista', __name__)

ESTADOS = {
    'cursando': 'Cursando',
    'abandono': 'Abandonó',
    'baja': 'Se dió de baja',
}


@vista_bp.route('/vista')
@admin_required
def index():
    bloqueo = exige_permiso(PERMISO_NOTAS_LEER)

    if bloqueo:
        return bloqueo

    cursada = elegida(_token())
    resultado = servicio.vista(_token(), cursada['id']) if cursada.get('id') else {'ok': True, 'datos': {}}

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    datos = resultado.get('datos') or {}
    categorias = datos.get('categorias') or []
    alumnos = datos.get('alumnos') or []
    criterio = {
        str(instancia['id']): categoria.get('criterio')
        for categoria in categorias
        for instancia in categoria.get('instancias') or []
    }

    for alumno in alumnos:
        alumno['estado_etiqueta'] = ESTADOS.get(alumno.get('estado'), alumno.get('estado') or '')

        for clave, celda in (alumno.get('notas') or {}).items():
            celda['valor'] = valor_celda(criterio.get(str(clave)), celda.get('nota'), celda.get('estado'))

    return render_template(
        'admin/vista.html',
        categorias=categorias,
        alumnos=alumnos,
        columnas=4 + sum(len(categoria.get('instancias') or []) * 2 for categoria in categorias),
        error=None if resultado.get('ok') else resultado.get('error'),
        **contexto_admin('vista'),
    )
