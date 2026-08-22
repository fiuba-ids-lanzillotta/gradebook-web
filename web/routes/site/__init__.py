"""Blueprint padre para la zona estudiante del sitio.

Anida sub-blueprints definidos en otros módulos para mantener cada
sección en su propio archivo.
"""
from flask import Blueprint

from web.routes.site.home import home_bp
from web.routes.site.items import items_bp

site_bp = Blueprint('site', __name__)
site_bp.register_blueprint(home_bp)
site_bp.register_blueprint(items_bp)
