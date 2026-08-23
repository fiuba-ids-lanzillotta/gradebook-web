"""Inicio del panel docente: listado de alumnos del cuatrimestre actual."""
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
)

from web.auth_sesion import admin_required, es_super_admin, redirigir_a_login_sin_sesion
from web.constants import CURSADA_ANIO, CURSADA_CUATRIMESTRE
from web.services.docentes import obtener_docente
from web.services import estudiantes as servicio

panel_bp = Blueprint('panel', __name__)

ESTADO_ETIQUETA = {
    'cursando': 'Cursando',
    'abandono': 'Abandonó',
    'baja': 'Se dió de baja',
}

SOLAPAS = (
    ('listado', 'Listado alumnos', 'nav-listado.svg', True),
    ('dashboards', 'Dashboards', 'nav-dashboards.svg', False),
    ('asistencia', 'Asistencia', 'nav-asistencia.svg', False),
    ('categorias', 'Categorías', 'nav-categorias.svg', False),
    ('registros', 'Registros', 'nav-registros.svg', False),
    ('docentes', 'Docentes', 'nav-docentes.svg', False),
    ('entregas', 'Entregas', 'nav-entregas.svg', False),
    ('vista', 'Vista general', 'nav-vista.svg', False),
)


def _token() -> str:
    return session.get('token') or ''


def _resultado_o_redirect(resultado):
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    if resultado.get('ok'):
        return redirect(url_for('web.admin.panel.index'))
    return None


def _nombre_docente() -> str:
    guardado = session.get('nombre_completo')
    if guardado:
        return guardado

    usuario = session.get('usuario') or {}
    docente_id = usuario.get('id')
    if not docente_id:
        return usuario.get('email') or ''

    docente = obtener_docente(_token(), docente_id)
    if docente.get('_unauthorized'):
        return usuario.get('email') or ''
    if docente.get('nombre') or docente.get('apellido'):
        nombre = f"{docente.get('nombre') or ''} {docente.get('apellido') or ''}".strip()
        session['nombre_completo'] = nombre
        return nombre

    return usuario.get('email') or ''


def _contexto_listado(listado: dict, error=None, ok=None):
    return {
        'estudiantes': listado.get('estudiantes') or [],
        'links': listado.get('links') or {},
        'paginacion': servicio.paginas_desde_links(
            listado.get('links') or {},
            listado.get('offset', 0),
            listado.get('limit', 10),
        ),
        'q': request.args.get('q', '').strip(),
        'error': error or listado.get('error'),
        'ok': ok,
        'es_super_admin': es_super_admin(),
        'nombre_docente': _nombre_docente(),
        'solapas': SOLAPAS,
        'estado_etiqueta': ESTADO_ETIQUETA,
        'cursada_anio': listado.get('anio', CURSADA_ANIO),
        'cursada_cuatrimestre': listado.get('cuatrimestre', CURSADA_CUATRIMESTRE),
    }


@panel_bp.route('/')
@admin_required
def index():
    q = request.args.get('q', '').strip()
    try:
        offset = max(int(request.args.get('_offset', 0)), 0)
    except (TypeError, ValueError):
        offset = 0
    try:
        limit = max(int(request.args.get('_limit', 10)), 1)
    except (TypeError, ValueError):
        limit = 10

    listado = servicio.listar_de_cursada(_token(), q=q, offset=offset, limit=limit)
    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return render_template(
        'admin/panel.html',
        **_contexto_listado(listado, error=None if listado.get('ok') else listado.get('error')),
    )

@panel_bp.route('/alumnos', methods=['POST'])
@admin_required
def agregar():
    resultado = servicio.crear_estudiante(_token(), request.form)
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    if resultado.get('ok'):
        flash('Alumno agregado e inscripto en el cuatrimestre vigente.', 'ok')
        padron = (request.form.get('padron') or '').strip()
        return redirect(url_for('web.admin.panel.index', q=padron))
    flash(resultado.get('error') or 'No se pudo agregar al alumno.', 'error')
    return redirect(url_for('web.admin.panel.index'))

@panel_bp.route('/alumnos/csv', methods=['POST'])
@admin_required
def publicar_csv():
    archivo = request.files.get('archivo')
    if archivo is None or not archivo.filename:
        flash('Elegí un archivo CSV.', 'error')
        return redirect(url_for('web.admin.panel.index'))

    resultado = servicio.importar_csv(_token(), archivo)
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    if resultado.get('ok'):
        resumen = resultado.get('resumen') or {}
        flash(
            f"CSV publicado. Nuevos: {resumen.get('estudiantes_creados', 0)}. "
            f"Inscriptos: {resumen.get('inscriptos', 0)}.",
            'ok',
        )
        return redirect(url_for('web.admin.panel.index'))

    listado = servicio.listar_de_cursada(_token())
    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/csv', methods=['GET'])
@admin_required
def descargar_csv():
    resultado = servicio.exportar_csv(_token())
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    if not resultado.get('ok'):
        flash(resultado.get('error') or 'No se pudo descargar el CSV.', 'error')
        return redirect(url_for('web.admin.panel.index'))

    return Response(
        resultado['contenido'],
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{resultado["nombre"]}"'},
    )


@panel_bp.route('/alumnos/<int:estudiante_id>/editar', methods=['POST'])
@admin_required
def editar(estudiante_id):
    resultado = servicio.actualizar_estudiante(_token(), estudiante_id, request.form)
    redireccion = _resultado_o_redirect(resultado)
    if redireccion:
        if resultado.get('ok'):
            flash('Datos del alumno actualizados.', 'ok')
        return redireccion

    listado = servicio.listar_de_cursada(_token())
    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/<int:estudiante_id>/abandonar', methods=['POST'])
@admin_required
def abandonar(estudiante_id):
    resultado = servicio.cambiar_estado(_token(), estudiante_id, 'abandono')
    redireccion = _resultado_o_redirect(resultado)
    if redireccion:
        if resultado.get('ok'):
            flash('Se marcó que el alumno abandonó la materia.', 'ok')
        return redireccion

    listado = servicio.listar_de_cursada(_token())
    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/<int:estudiante_id>/baja', methods=['POST'])
@admin_required
def dar_de_baja(estudiante_id):
    motivo = (request.form.get('motivo') or '').strip()
    if not motivo:
        flash('La razón es obligatoria para dar de baja.', 'error')
        return redirect(url_for('web.admin.panel.index'))

    resultado = servicio.cambiar_estado(_token(), estudiante_id, 'baja', motivo)
    redireccion = _resultado_o_redirect(resultado)
    if redireccion:
        if resultado.get('ok'):
            flash('Alumno dado de baja.', 'ok')
        return redireccion

    listado = servicio.listar_de_cursada(_token())
    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/<int:estudiante_id>/alta', methods=['POST'])
@admin_required
def dar_de_alta(estudiante_id):
    if not es_super_admin():
        flash('Solo un superadmin puede dar de alta a un alumno.', 'error')
        return redirect(url_for('web.admin.panel.index'))

    resultado = servicio.cambiar_estado(_token(), estudiante_id, 'cursando')
    redireccion = _resultado_o_redirect(resultado)
    if redireccion:
        if resultado.get('ok'):
            flash('Alumno dado de alta de nuevo.', 'ok')
        return redireccion

    listado = servicio.listar_de_cursada(_token())
    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/<int:estudiante_id>')
@admin_required
def perfil(estudiante_id):
    """Placeholder: el perfil con notas del cuatrimestre actual se arma después."""
    return redirect(url_for('web.admin.panel.index'))