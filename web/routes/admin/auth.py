"""Autenticación: login, logout y reexport de los decoradores."""
from flask import Blueprint, render_template, request, redirect, session, url_for
from web.services.auth import autenticar, obtener_identidad, solicitar_recuperacion, confirmar_recuperacion
from web.constants import RECAPTCHA_SITE_KEY
from web.auth_sesion import (
    admin_required,
    redirigir_a_login_sin_sesion,
    url_post_login,
)

auth_bp = Blueprint('auth', __name__)


def _captcha_token() -> str:
    return request.form.get('g-recaptcha-response', '').strip()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('token'):
        return redirect(url_post_login())

    error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        resultado = autenticar(email, password, recaptcha_token=_captcha_token())

        if resultado['ok']:
            session['token'] = resultado['token']
            usuario = dict(resultado['usuario'] or {})
            identidad = obtener_identidad(resultado['token'])
            usuario['permisos'] = list(identidad.get('permisos') or [])
            print(usuario['permisos'])
            session['usuario'] = usuario

            return redirect(url_post_login())

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
MENSAJE_CAMBIO_OK = 'Tu contraseña se actualizó. Ya podés iniciar sesión.'


@auth_bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    error = None
    ok = None
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            error = 'Ingresá un correo electrónico.'
        else:
            resultado = solicitar_recuperacion(email)
            # Misma respuesta siempre (no revela si el mail existe); sólo un
            # error de conexión rompe la uniformidad.
            if resultado['ok']:
                ok = MENSAJE_RECUPERAR
            else:
                error = resultado['error']

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
            resultado = confirmar_recuperacion(token, password)
            if resultado['ok']:
                ok = MENSAJE_CAMBIO_OK
            else:
                error = resultado['error']

    return render_template(
        'admin/cambiar_contrasena.html',
        token=token,
        error=error,
        ok=ok,
    )