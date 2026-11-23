"""Pantalla admin: registro de auditoría."""
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template, request

from web.auth_sesion import admin_required, exige_permiso, redirigir_a_login_sin_sesion
from web.constants import PERMISO_REGISTROS_LEER
from web.routes.admin.panel import _token, contexto_admin
from web.services import registros as servicio
from web.services.estudiantes import paginas_desde_links

registros_bp = Blueprint('registros', __name__)

ZONA = ZoneInfo('America/Argentina/Buenos_Aires')
LIMITE = 8
ACCIONES = (
    ('evaluaciones.crear', 'Crear categoría'),
    ('evaluaciones.grupos', 'Habilitar creación de equipos'),
    ('evaluaciones.visibilidad', 'Cambiar visibilidad'),
    ('grupos.crear', 'Crear equipo'),
    ('grupos.renombrar', 'Renombrar equipo'),
    ('grupos.integrante.agregar', 'Agregar integrante'),
    ('grupos.integrante.echar', 'Echar integrante'),
    ('grupos.integrante.transferir', 'Transferir integrante'),
    ('grupos.tutores', 'Asignar tutores'),
    ('estudiantes.crear', 'Alta de alumno'),
    ('estudiantes.editar', 'Editar alumno'),
    ('estudiantes.baja', 'Baja de alumno'),
    ('estudiantes.abandono', 'Abandono'),
    ('estudiantes.reactivar', 'Reactivar alumno'),
    ('estudiantes.csv', 'Publicar CSV'),
    ('cursadas.crear', 'Crear cursada'),
    ('cursadas.editar', 'Editar cursada'),
    ('docentes.crear', 'Alta de docente'),
    ('docentes.editar', 'Editar docente'),
    ('docentes.eliminar', 'Desactivar docente'),
    ('asistencia.tomar', 'Tomar asistencia'),
    ('asistencia.enviar_qrs', 'Enviar QRs'),
    ('asistencia.cerrar', 'Cerrar asistencia'),
    ('instancias.crear', 'Crear instancia'),
)


def _horario(valor) -> str:
    if not valor:
        return ''

    texto = str(valor).replace('Z', '+00:00')

    try:
        momento = datetime.fromisoformat(texto)
    except ValueError:
        return texto[:16].replace('T', ' ')

    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=ZoneInfo('UTC'))

    return momento.astimezone(ZONA).strftime('%d/%m/%Y %H:%M')


def _usuario(email: str) -> str:
    return (email or '').strip().split('@', 1)[0]


def _iniciales(email: str) -> str:
    local = (email or '').split('@', 1)[0]
    partes = [parte for parte in re.split(r'[.\-_]+', local) if parte]
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    limpio = re.sub(r'[^A-Za-z0-9]', '', local)
    return (limpio[:2] or '?').upper()


_ROL_CLASE = {
    'Profesor': 'profesor',
    'Ayudante': 'ayudante',
    'Colaborador': 'colaborador',
    'Alumno': 'alumno',
}


@registros_bp.route('/registros')
@admin_required
def index():
    bloqueo = exige_permiso(PERMISO_REGISTROS_LEER)

    if bloqueo:
        return bloqueo

    email = (request.args.get('email') or '').strip()
    accion = (request.args.get('accion') or '').strip()
    tipo = (request.args.get('tipo') or '').strip()
    orden = 'asc' if request.args.get('orden') == 'asc' else 'desc'

    try:
        offset = max(int(request.args.get('_offset', 0)), 0)
    except (TypeError, ValueError):
        offset = 0

    resultado = servicio.listar(
        _token(), email=email, accion=accion, tipo=tipo, orden=orden, offset=offset, limit=LIMITE,
    )

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    datos = resultado.get('datos') or {}
    filas = [
        {
            'usuario': _usuario(fila.get('actor_email') or ''),
            'iniciales': _iniciales(fila.get('actor_email') or ''),
            'rol': fila.get('rol') or '',
            'rol_clase': _ROL_CLASE.get(fila.get('rol') or '', 'docente'),
            'accion': fila.get('descripcion') or fila.get('accion') or '',
            'horario': _horario(fila.get('created_at')),
        }
        for fila in (datos.get('registros') or [])
    ]
    links = datos.get('_links') or {}

    return render_template(
        'admin/registros.html',
        filas=filas,
        acciones=ACCIONES,
        email=email,
        accion=accion,
        tipo=tipo,
        orden=orden,
        paginacion=paginas_desde_links(links, offset, LIMITE),
        error=None if resultado.get('ok') else resultado.get('error'),
        **contexto_admin('registros'),
    )
