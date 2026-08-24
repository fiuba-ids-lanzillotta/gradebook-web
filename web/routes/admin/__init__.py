"""Blueprint padre para la zona de administración (requiere login).

Anida sub-blueprints definidos en otros módulos para mantener cada
sección en su propio archivo.
"""
from flask import Blueprint

from web.routes.admin.auth import auth_bp
from web.routes.admin.panel import panel_bp
from web.routes.admin.asistencia import asistencia_bp
from web.routes.admin.items import items_bp

admin_bp = Blueprint('admin', __name__)
admin_bp.register_blueprint(auth_bp)
admin_bp.register_blueprint(panel_bp)
admin_bp.register_blueprint(asistencia_bp)
admin_bp.register_blueprint(items_bp)
