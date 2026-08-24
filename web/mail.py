from flask_mail import Mail

from web.constants import (
    MAIL_DEFAULT_SENDER,
    MAIL_PASSWORD,
    MAIL_PORT,
    MAIL_SERVER,
    MAIL_SUPPRESS_SEND,
    MAIL_USE_SSL,
    MAIL_USE_TLS,
    MAIL_USERNAME,
)

mail = Mail()


def mail_configurado() -> bool:
    return bool(MAIL_USERNAME and MAIL_PASSWORD) and not MAIL_SUPPRESS_SEND


def configurar_mail(app) -> None:
    app.config['MAIL_SERVER'] = MAIL_SERVER
    app.config['MAIL_PORT'] = MAIL_PORT
    app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
    app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
    app.config['MAIL_USERNAME'] = MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER or 'noreply@localhost'
    app.config['MAIL_SUPPRESS_SEND'] = MAIL_SUPPRESS_SEND or not mail_configurado()
    mail.init_app(app)