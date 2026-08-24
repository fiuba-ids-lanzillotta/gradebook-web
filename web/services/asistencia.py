"""Toma de asistencia (fase visual): mails desde el web, sin QR ni persistencia."""
import logging

from flask import render_template
from flask_mail import Message

from web.mail import mail, mail_configurado
from web.services import estudiantes

logger = logging.getLogger(__name__)


def notificar_toma_asistencia(token: str) -> dict:
    """GET paginado de alumnos de la cursada vigente y un mail a cada email."""
    listado = _todos_de_cursada(token)
    if not listado.get('ok'):
        return listado

    enviados = 0
    omitidos = 0
    errores = 0
    anio = listado.get('anio')
    cuatrimestre = listado.get('cuatrimestre')
    simulado = not mail_configurado()

    for alumno in listado.get('estudiantes') or []:
        email = (alumno.get('email') or '').strip()
        estado = alumno.get('estado') or 'cursando'
        if not email or estado != 'cursando':
            omitidos += 1
            continue

        nombre = f"{alumno.get('nombre') or ''} {alumno.get('apellido') or ''}".strip() or 'alumno/a'
        try:
            _enviar_aviso(email, nombre, anio, cuatrimestre, simulado=simulado)
            enviados += 1
        except Exception as error:
            logger.error(f"No se pudo avisar a {email}: {error}")
            errores += 1

    return {
        'ok': True,
        'enviados': enviados,
        'omitidos': omitidos,
        'errores': errores,
        'simulado': simulado,
    }


def _todos_de_cursada(token: str) -> dict:
    """Recorre GET /estudiantes de la cursada vigente (el DTO trae email)."""
    todos = []
    offset = 0
    limit = 100
    anio = None
    cuatrimestre = None
    while True:
        pagina = estudiantes.listar_de_cursada(token, q='', offset=offset, limit=limit)
        if not pagina.get('ok'):
            return pagina
        anio = pagina.get('anio', anio)
        cuatrimestre = pagina.get('cuatrimestre', cuatrimestre)
        lote = pagina.get('estudiantes') or []
        todos.extend(lote)
        if not (pagina.get('links') or {}).get('_next') or not lote:
            break
        offset += limit
    return {'ok': True, 'estudiantes': todos, 'anio': anio, 'cuatrimestre': cuatrimestre}


def _enviar_aviso(destinatario: str, nombre: str, anio, cuatrimestre, simulado: bool) -> None:
    html = render_template(
        'emails/asistencia.html',
        nombre=nombre,
        anio=anio,
        cuatrimestre=cuatrimestre,
    )
    if simulado:
        logger.warning(f'[asistencia] Mail deshabilitado; aviso para {destinatario}')
        return

    mensaje = Message(
        subject='Se está tomando asistencia — Intro. Desarrollo de Software',
        recipients=[destinatario],
        html=html,
    )
    mail.send(mensaje)