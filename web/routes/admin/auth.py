"""Autenticación del panel de administración: login, logout y el
decorador admin_required que protege las secciones internas.

El login delega la verificación de credenciales en la API (gradebook-api),
que devuelve un JWT. Ese token se guarda en la sesión y se usará para autorizar
las operaciones de administración contra la API.
"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session

from web.services.auth import autenticar
from web.constants import RECAPTCHA_SITE_KEY

auth_bp = Blueprint('auth', __name__)

def _captcha_token() -> str:
    return request.form.get('g-recaptcha-response', '').strip()

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('token'):
            return redirect(url_for('web.admin.auth.login'))

        return view(*args, **kwargs)
    return wrapped


def redirigir_a_login_sin_sesion():
    """Limpia la sesión y redirige al login (p. ej. cuando la API responde 401/403)."""
    session.pop('token', None)
    session.pop('usuario', None)

    return redirect(url_for('web.admin.auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('token'):
        return redirect(url_for('web.admin.panel.index'))

    error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        resultado = autenticar(email, password, recaptcha_token=_captcha_token())
        if resultado['ok']:
            session['token'] = resultado['token']
            session['usuario'] = resultado['usuario']
            return redirect(url_for('web.admin.panel.index'))
        error = resultado['error']

    return render_template(
        'admin/login.html',
        error=error,
        recaptcha_site_key=RECAPTCHA_SITE_KEY,
    )


@auth_bp.route('/logout')
def logout():
    return redirigir_a_login_sin_sesion()

MENSAJE_RECUPERAR = (
    'Si el correo está registrado, vas a recibir un enlace '
    'para restablecer la contraseña.'
)
MENSAJE_CAMBIO_PENDIENTE = (
    'El cambio de contraseña todavía no está disponible. '
    'Cuando la API exponga el reset, este formulario lo va a completar.'
)


@auth_bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    error = None
    ok = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            error = 'Ingresá un correo electrónico.'
        else:
            # Misma respuesta siempre: no revelar si el mail existe.
            # Cuando exista POST /password-reset/solicitar, llamarlo acá
            # y seguir mostrando MENSAJE_RECUPERAR.
            ok = MENSAJE_RECUPERAR

    return render_template('admin/recuperar.html', error=error, ok=ok)


@auth_bp.route('/cambiar-contrasena', methods=['GET', 'POST'])
def cambiar_contrasena():
    token = (request.values.get('token') or '').strip()
    error = None
    ok = None

    if not token:
        error = 'El enlace no es válido o expiró. Solicitá uno nuevo.'
        return render_template(
            'admin/cambiar_contrasena.html',
            token='',
            error=error,
            ok=ok,
        )

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('password_confirm', '')
        if not password or not confirm:
            error = 'Completá ambos campos.'
        elif password != confirm:
            error = 'Las contraseñas no coinciden.'
        else:
            # Acá irá POST /password-reset/confirmar {token, password}.
            ok = MENSAJE_CAMBIO_PENDIENTE

    return render_template(
        'admin/cambiar_contrasena.html',
        token=token,
        error=error,
        ok=ok,
    )