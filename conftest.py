"""
Config compartida de pytest.

Fija variables de entorno dummy antes de importar la app y ofrece una fixture
para construir respuestas HTTP falsas (los tests mockean `requests`, no hacen red).
"""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('API_BASE_URL', 'http://api.test/gradebook_api')

# Raíz de los mocks JSON usados por los tests (respuestas de la API guardadas en
# archivos, ver tests/resources/json/<dominio>/<nombre>.json).
_RECURSOS = Path(__file__).parent / 'tests' / 'resources'


@pytest.fixture
def cargar_json():
    """Carga un mock JSON desde tests/resources (p. ej. 'json/items/lista.json')."""
    def _cargar(ruta_relativa):
        return json.loads((_RECURSOS / ruta_relativa).read_text(encoding='utf-8'))

    return _cargar


@pytest.fixture
def respuesta_falsa():
    """Factory de respuestas HTTP falsas compatibles con lo que usan los services."""
    def _crear(status_code, json_data=None, content=b'', headers=None):
        return SimpleNamespace(
            status_code=status_code,
            json=lambda: json_data,
            content=content,
            headers=headers or {},
        )

    return _crear
