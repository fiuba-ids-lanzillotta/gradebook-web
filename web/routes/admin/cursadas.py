"""Pantalla admin: Cursada — cuatrimestre actual e historial de cursadas."""
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
    redirigir_a_login_sin_sesion,
    redirigir_sin_permiso,
    tiene_permiso,
)
from web.constants import (
    PERMISO_CURSADAS_CREAR,
    PERMISO_CURSADAS_LEER,
    PERMISO_CURSADAS_MODIFICAR,
)
from web.routes.admin.panel import _token, contexto_admin
from web.services import cursos as servicio

cursadas_bp = Blueprint('cursadas', __name__)


def _exige(permiso: str):
    if tiene_permiso(permiso):
        return None

    return redirigir_sin_permiso()


def _fecha_txt(fecha: str) -> str:
    fecha = str(fecha or '')[:10]

    if len(fecha) == 10 and fecha[4] == '-' and fecha[7] == '-':
        return f'{fecha[8:10]}/{fecha[5:7]}/{fecha[0:4]}'

    return fecha


def _ordenar(cursadas: list[dict]) -> list[dict]:
    """Más reciente primero."""
    return sorted(
        cursadas,
        key=lambda fila: (str(fila.get('anio') or ''), str(fila.get('cuatrimestre') or '')),
        reverse=True,
    )


def _materias(cursadas: list[dict]) -> dict:
    """{codigo: nombre} para autocompletar el alta de cursada."""
    materias = {}

    for cursada in cursadas:
        codigo = cursada.get('codigo')

        if codigo and codigo not in materias:
            materias[codigo] = cursada.get('nombre') or ''

    return materias


@cursadas_bp.route('/cursadas')
@admin_required
def index():
    bloqueo = _exige(PERMISO_CURSADAS_LEER)

    if bloqueo:
        return bloqueo

    resultado = servicio.listar_cursadas(_token())

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    cursadas = _ordenar(resultado.get('cursadas') or [])
    vigente = next((fila for fila in cursadas if fila.get('vigente')), None)

    for fila in cursadas:
        fila['inicio_txt'] = _fecha_txt(fila.get('fecha_inicio'))
        fila['fin_txt'] = _fecha_txt(fila.get('fecha_fin'))

    return render_template(
        'admin/cursadas.html',
        cursadas=cursadas,
        vigente=vigente,
        materias=_materias(cursadas),
        puede_crear=tiene_permiso(PERMISO_CURSADAS_CREAR),
        puede_editar=tiene_permiso(PERMISO_CURSADAS_MODIFICAR),
        error=None if resultado.get('ok') else resultado.get('error'),
        **contexto_admin('cursada'),
    )


@cursadas_bp.route('/cursadas', methods=['POST'])
@admin_required
def crear():
    bloqueo = _exige(PERMISO_CURSADAS_CREAR)

    if bloqueo:
        return bloqueo

    resultado = servicio.crear_cursada(_token(), request.form)

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if resultado.get('ok'):
        flash('Cursada creada.', 'ok')
    else:
        flash(resultado.get('error') or 'No se pudo crear la cursada.', 'error')

    return redirect(url_for('web.admin.cursadas.index'))


@cursadas_bp.route('/cursadas/<int:cursada_id>', methods=['POST'])
@admin_required
def editar(cursada_id):
    bloqueo = _exige(PERMISO_CURSADAS_MODIFICAR)

    if bloqueo:
        return bloqueo

    resultado = servicio.actualizar_cursada(_token(), cursada_id, request.form)

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if resultado.get('ok'):
        flash('Cursada actualizada.', 'ok')
    else:
        flash(resultado.get('error') or 'No se pudo actualizar la cursada.', 'error')

    return redirect(url_for('web.admin.cursadas.index'))
