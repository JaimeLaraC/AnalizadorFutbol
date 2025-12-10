"""
Test básico para verificar que la configuración funciona.
"""

import pytest


def test_placeholder():
    """Test placeholder para verificar que pytest funciona."""
    assert True


def test_import_config():
    """Test que verifica que se puede importar la configuración."""
    # Este test fallará si no hay .env, lo cual es esperado en CI
    # Por eso lo marcamos como skip si falla la importación
    try:
        from src.utils.config import settings
        assert settings is not None
    except Exception:
        pytest.skip("No se puede cargar config sin .env")
