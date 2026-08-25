"""Pantalla admin: docentes (template, sin cablear la API todavía)."""
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from web.auth_sesion import admin_required, es_super_admin
from web.routes.admin.panel import contexto_admin

docentes_bp = Blueprint('docentes', __name__)

CARGOS = ('Profesor', 'Ayudante', 'Colaborador')

PERMISOS_CATALOGO = (
    {'codigo': 'docentes.leer', 'descripcion': 'Ver docentes'},
    {'codigo': 'docentes.gestionar', 'descripcion': 'Alta, edición y desactivar docentes'},
    {'codigo': 'estudiantes.leer', 'descripcion': 'Ver alumnos'},
    {'codigo': 'estudiantes.gestionar', 'descripcion': 'Alta, edición, baja y abandono de alumnos'},
    {'codigo': 'cursadas.leer', 'descripcion': 'Ver cursadas'},
    {'codigo': 'asistencias.leer', 'descripcion': 'Ver asistencia'},
    {'codigo': 'asistencias.gestionar', 'descripcion': 'Tomar asistencia'},
    {'codigo': 'roles.gestionar', 'descripcion': 'Configurar permisos por rol'},
    {'codigo': 'permisos.asignar', 'descripcion': 'Asignar o revocar permisos por persona'},
)

_TODOS = [item['codigo'] for item in PERMISOS_CATALOGO]
_SIN_DOCENTE_NI_RBAC = [
    codigo for codigo in _TODOS
    if codigo not in ('docentes.gestionar', 'roles.gestionar', 'permisos.asignar')
]
PERMISOS_POR_CARGO = {
    'Profesor': list(_TODOS),
    'Ayudante': list(_SIN_DOCENTE_NI_RBAC),
    'Colaborador': list(_SIN_DOCENTE_NI_RBAC),
}

_SEMILLA = (
    {
        'id': 1,
        'nombre': 'Bruno',
        'apellido': 'Lanzillotta',
        'email': 'blanzillotta@fi.uba.ar',
        'rol': 'Profesor',
        'activo': True,
        'permisos': list(PERMISOS_POR_CARGO['Profesor']),
    },
    {
        'id': 2,
        'nombre': 'Leonel',
        'apellido': 'Chaves',
        'email': 'lchaves@fi.uba.ar',
        'rol': 'Ayudante',
        'activo': True,
        'permisos': list(PERMISOS_POR_CARGO['Ayudante']),
    },
    {
        'id': 3,
        'nombre': 'Valentina',
        'apellido': 'Grobly',
        'email': 'vgrobly@fi.uba.ar',
        'rol': 'Colaborador',
        'activo': True,
        'permisos': list(PERMISOS_POR_CARGO['Colaborador']),
    },
)


def _solo_profesor():
    if not es_super_admin():
        flash('Solo un profesor puede administrar docentes.', 'error')
        return redirect(url_for('web.admin.panel.index'))
    return None


def _listado() -> list[dict]:
    if 'docentes_ui' not in session:
        session['docentes_ui'] = [dict(fila) for fila in _SEMILLA]
        session.modified = True
    return session['docentes_ui']


def _guardar(filas: list[dict]) -> None:
    session['docentes_ui'] = filas
    session.modified = True


def _buscar(docente_id: int) -> dict | None:
    for fila in _listado():
        if fila['id'] == docente_id:
            return fila
    return None


def _email_usado(email: str, excluir_id: int | None = None) -> bool:
    email_norm = (email or '').strip().lower()
    for fila in _listado():
        if fila['id'] == excluir_id:
            continue
        if (fila.get('email') or '').lower() == email_norm:
            return True
    return False


def _contexto_pantalla(**extra) -> dict:
    docentes = sorted(_listado(), key=lambda fila: (fila['apellido'] or '', fila['nombre'] or ''))
    return {
        **contexto_admin('docentes'),
        'docentes': docentes,
        'cargos': CARGOS,
        'permisos_catalogo': PERMISOS_CATALOGO,
        'permisos_por_cargo': PERMISOS_POR_CARGO,
        **extra,
    }


@docentes_bp.route('/docentes')
@admin_required
def index():
    bloqueo = _solo_profesor()
    if bloqueo:
        return bloqueo
    return render_template('admin/docentes.html', **_contexto_pantalla())


@docentes_bp.route('/docentes', methods=['POST'])
@admin_required
def crear():
    bloqueo = _solo_profesor()
    if bloqueo:
        return bloqueo

    nombre = (request.form.get('nombre') or '').strip()
    apellido = (request.form.get('apellido') or '').strip()
    email = (request.form.get('email') or '').strip()
    rol = (request.form.get('rol') or '').strip()

    if not (nombre and apellido and email and rol in CARGOS):
        flash('Completá nombre, apellido, correo y rol.', 'error')
        return redirect(url_for('web.admin.docentes.index'))
    if _email_usado(email):
        flash('Ya hay un docente con ese correo.', 'error')
        return redirect(url_for('web.admin.docentes.index'))

    filas = _listado()
    nuevo_id = max((fila['id'] for fila in filas), default=0) + 1
    filas.append({
        'id': nuevo_id,
        'nombre': nombre,
        'apellido': apellido,
        'email': email,
        'rol': rol,
        'activo': True,
        'permisos': list(PERMISOS_POR_CARGO[rol]),
    })
    _guardar(filas)
    flash(f'Se agregó a {apellido}, {nombre} ({rol}). El mail con la clave se cablea después.', 'ok')
    return redirect(url_for('web.admin.docentes.index'))


@docentes_bp.route('/docentes/<int:docente_id>', methods=['POST'])
@admin_required
def editar(docente_id):
    bloqueo = _solo_profesor()
    if bloqueo:
        return bloqueo

    fila = _buscar(docente_id)
    if not fila:
        flash('No se encontró ese docente.', 'error')
        return redirect(url_for('web.admin.docentes.index'))

    nombre = (request.form.get('nombre') or '').strip()
    apellido = (request.form.get('apellido') or '').strip()
    email = (request.form.get('email') or '').strip()
    rol = (request.form.get('rol') or '').strip()
    if not (nombre and apellido and email and rol in CARGOS):
        flash('Completá nombre, apellido, correo y rol.', 'error')
        return redirect(url_for('web.admin.docentes.index'))
    if _email_usado(email, excluir_id=docente_id):
        flash('Ya hay un docente con ese correo.', 'error')
        return redirect(url_for('web.admin.docentes.index'))

    if rol == 'Profesor':
        permisos = list(PERMISOS_POR_CARGO['Profesor'])
    else:
        tildados = set(request.form.getlist('permisos'))
        permisos = [item['codigo'] for item in PERMISOS_CATALOGO if item['codigo'] in tildados]

    fila.update({
        'nombre': nombre,
        'apellido': apellido,
        'email': email,
        'rol': rol,
        'permisos': permisos,
    })
    _guardar(_listado())
    flash(f'Se actualizó a {apellido}, {nombre}.', 'ok')
    return redirect(url_for('web.admin.docentes.index'))


@docentes_bp.route('/docentes/<int:docente_id>/desactivar', methods=['POST'])
@admin_required
def desactivar(docente_id):
    bloqueo = _solo_profesor()
    if bloqueo:
        return bloqueo
    fila = _buscar(docente_id)
    if not fila:
        flash('No se encontró ese docente.', 'error')
        return redirect(url_for('web.admin.docentes.index'))
    if fila['rol'] == 'Profesor':
        flash('No se puede desactivar a un profesor.', 'error')
        return redirect(url_for('web.admin.docentes.index'))
    fila['activo'] = False
    _guardar(_listado())
    flash(f'{fila["apellido"]}, {fila["nombre"]} quedó inactivo.', 'ok')
    return redirect(url_for('web.admin.docentes.index'))


@docentes_bp.route('/docentes/<int:docente_id>/reactivar', methods=['POST'])
@admin_required
def reactivar(docente_id):
    bloqueo = _solo_profesor()
    if bloqueo:
        return bloqueo
    fila = _buscar(docente_id)
    if not fila:
        flash('No se encontró ese docente.', 'error')
        return redirect(url_for('web.admin.docentes.index'))
    fila['activo'] = True
    _guardar(_listado())
    flash(f'{fila["apellido"]}, {fila["nombre"]} volvió a estar activo.', 'ok')
    return redirect(url_for('web.admin.docentes.index'))