"""Pantalla admin: equipos de la cursada elegida."""
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from web.auth_sesion import (
    admin_required,
    exige_permiso,
    redirigir_a_login_sin_sesion,
    tiene_permiso,
    volver_con_mensaje,
)
from web.constants import PERMISO_ESTUDIANTES_LEER, PERMISO_ESTUDIANTES_MODIFICAR
from web.cursada_filtro import elegida
from web.routes.admin.panel import _token, contexto_admin
from web.services import grupos as servicio
from web.services.docentes import listar_docentes

grupos_bp = Blueprint('grupos', __name__)


def _docentes_activos() -> list[dict]:
    resultado = listar_docentes(_token())
    filas = (resultado.get('docentes') or []) if resultado.get('ok') else []

    return sorted(
        [fila for fila in filas if fila.get('activo') is not False],
        key=lambda fila: (fila.get('apellido') or '', fila.get('nombre') or ''),
    )


def _cursada_id():
    return elegida(_token()).get('id')


@grupos_bp.route('/equipos')
@admin_required
def index():
    bloqueo = exige_permiso(PERMISO_ESTUDIANTES_LEER)

    if bloqueo:
        return bloqueo

    cursada_id = _cursada_id()
    resultado = servicio.listar(_token(), cursada_id) if cursada_id else {'ok': True, 'datos': {'grupos': []}}

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    grupos = (resultado.get('datos') or {}).get('grupos') or []
    evaluaciones = []

    for grupo in grupos:
        nombre = (grupo.get('evaluacion_nombre') or '').strip()

        if nombre and nombre not in evaluaciones:
            evaluaciones.append(nombre)

    return render_template(
        'admin/equipos.html',
        grupos=grupos,
        evaluaciones=evaluaciones,
        docentes=_docentes_activos(),
        puede_editar=tiene_permiso(PERMISO_ESTUDIANTES_MODIFICAR),
        error=None if resultado.get('ok') else resultado.get('error'),
        **contexto_admin('equipos'),
    )


@grupos_bp.route('/equipos/tutores', methods=['POST'])
@admin_required
def guardar_tutores():
    bloqueo = exige_permiso(PERMISO_ESTUDIANTES_MODIFICAR)

    if bloqueo:
        return bloqueo

    asignaciones = []

    for clave, valor in request.form.items():
        if clave.startswith('tutor_') and clave[6:].isdigit():
            asignaciones.append({
                'grupo_id': int(clave[6:]),
                'tutor_id': int(valor) if str(valor).isdigit() else None,
            })

    resultado = servicio.guardar_tutores(_token(), asignaciones)

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if resultado.get('ok'):
        sin_tutor = (resultado.get('datos') or {}).get('sin_tutor') or 0
        flash('Tutores guardados.', 'ok')

        if sin_tutor == 1:
            flash('1 equipo quedó sin tutor.', 'error')
        elif sin_tutor:
            flash(f'{sin_tutor} equipos quedaron sin tutor.', 'error')
    else:
        flash(resultado.get('error') or 'No se pudieron guardar los tutores.', 'error')

    return redirect(url_for('web.admin.grupos.index'))


@grupos_bp.route('/equipos/<int:grupo_id>')
@admin_required
def detalle(grupo_id):
    bloqueo = exige_permiso(PERMISO_ESTUDIANTES_LEER)

    if bloqueo:
        return bloqueo

    resultado = servicio.obtener(_token(), grupo_id)

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    grupo = resultado.get('datos') or {}

    return render_template(
        'admin/equipo.html',
        grupo=grupo,
        puede_editar=tiene_permiso(PERMISO_ESTUDIANTES_MODIFICAR),
        error=None if resultado.get('ok') else resultado.get('error'),
        **contexto_admin('equipos'),
    )


@grupos_bp.route('/equipos/<int:grupo_id>/nombre', methods=['POST'])
@admin_required
def renombrar(grupo_id):
    bloqueo = exige_permiso(PERMISO_ESTUDIANTES_MODIFICAR)

    if bloqueo:
        return bloqueo

    resultado = servicio.renombrar(_token(), grupo_id, request.form.get('nombre') or '')

    return _volver(resultado, grupo_id, 'Nombre actualizado.')


@grupos_bp.route('/equipos/<int:grupo_id>/integrantes', methods=['POST'])
@admin_required
def agregar(grupo_id):
    bloqueo = exige_permiso(PERMISO_ESTUDIANTES_MODIFICAR)

    if bloqueo:
        return bloqueo

    estudiante_id = request.form.get('estudiante_id')
    resultado = servicio.agregar_integrante(
        _token(), grupo_id, int(estudiante_id) if str(estudiante_id).isdigit() else 0,
    )

    return _volver(resultado, grupo_id, 'Integrante agregado.')


@grupos_bp.route('/equipos/<int:grupo_id>/integrantes/<int:estudiante_id>/echar', methods=['POST'])
@admin_required
def echar(grupo_id, estudiante_id):
    bloqueo = exige_permiso(PERMISO_ESTUDIANTES_MODIFICAR)

    if bloqueo:
        return bloqueo

    resultado = servicio.echar_integrante(_token(), grupo_id, estudiante_id)

    return _volver(resultado, grupo_id, 'Integrante echado del equipo.')


@grupos_bp.route('/equipos/<int:grupo_id>/integrantes/<int:estudiante_id>/transferir', methods=['POST'])
@admin_required
def transferir(grupo_id, estudiante_id):
    bloqueo = exige_permiso(PERMISO_ESTUDIANTES_MODIFICAR)

    if bloqueo:
        return bloqueo

    destino = request.form.get('grupo_destino_id')
    resultado = servicio.transferir_integrante(
        _token(), grupo_id, estudiante_id, int(destino) if str(destino).isdigit() else 0,
    )

    return _volver(resultado, grupo_id, 'Integrante transferido.')


def _volver(resultado: dict, grupo_id: int, mensaje_ok: str):
    return volver_con_mensaje(
        resultado, mensaje_ok,
        url_for('web.admin.grupos.detalle', grupo_id=grupo_id),
    )
