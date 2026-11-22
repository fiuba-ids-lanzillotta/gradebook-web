"""Pantalla admin: categorías (evaluaciones) de la cursada elegida."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from web.auth_sesion import (
    admin_required,
    exige_permiso,
    redirigir_a_login_sin_sesion,
    tiene_permiso,
    volver_con_mensaje,
)
from web.constants import (
    PERMISO_EVALUACIONES_GESTIONAR,
    PERMISO_EVALUACIONES_LEER,
    PERMISO_GRUPOS_HABILITAR,
)
from web.cursada_filtro import elegida
from web.routes.admin.panel import _token, contexto_admin
from web.services import evaluaciones as servicio

categorias_bp = Blueprint('categorias', __name__)


def _volver(resultado: dict, mensaje_ok: str):
    return volver_con_mensaje(resultado, mensaje_ok, url_for('web.admin.categorias.index'))


@categorias_bp.route('/categorias')
@admin_required
def index():
    bloqueo = exige_permiso(PERMISO_EVALUACIONES_LEER)

    if bloqueo:
        return bloqueo

    cursada_id = elegida(_token()).get('id')
    resultado = servicio.listar(_token(), cursada_id) if cursada_id else {'ok': True, 'datos': {'evaluaciones': []}}

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return render_template(
        'admin/categorias.html',
        evaluaciones=(resultado.get('datos') or {}).get('evaluaciones') or [],
        puede_crear=tiene_permiso(PERMISO_EVALUACIONES_GESTIONAR),
        puede_habilitar=tiene_permiso(PERMISO_GRUPOS_HABILITAR),
        error=None if resultado.get('ok') else resultado.get('error'),
        **contexto_admin('categorias'),
    )


@categorias_bp.route('/categorias', methods=['POST'])
@admin_required
def crear():
    bloqueo = exige_permiso(PERMISO_EVALUACIONES_GESTIONAR)

    if bloqueo:
        return bloqueo

    cursada_id = elegida(_token()).get('id')

    if not cursada_id:
        flash('Elegí una cursada para agregar la categoría.', 'error')

        return redirect(url_for('web.admin.categorias.index'))

    resultado = servicio.crear(_token(), cursada_id, {
        'nombre': (request.form.get('nombre') or '').strip(),
        'tipo': request.form.get('tipo') or '',
        'criterio': request.form.get('criterio') or '',
        'peso': request.form.get('peso') or '',
        'modalidad': request.form.get('modalidad') or '',
        'instancias': request.form.get('instancias') or '',
        'requiere_corrector': '1' in request.form.getlist('requiere_corrector'),
    })

    return _volver(resultado, 'Categoría agregada.')


@categorias_bp.route('/categorias/<int:evaluacion_id>/grupos', methods=['POST'])
@admin_required
def grupos(evaluacion_id):
    bloqueo = exige_permiso(PERMISO_GRUPOS_HABILITAR)

    if bloqueo:
        return bloqueo

    habilitado = request.form.get('habilitado') == '1'
    resultado = servicio.habilitar_grupos(_token(), evaluacion_id, habilitado)
    mensaje = 'Creación de equipos habilitada.' if habilitado else 'Creación de equipos cerrada.'

    return _volver(resultado, mensaje)
