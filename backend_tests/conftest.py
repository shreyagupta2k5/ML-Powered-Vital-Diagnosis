# backend_tests/conftest.py
import pytest
# Configure pytest-asyncio to use 'auto' mode for all async tests
pytest_plugins = ['pytest_asyncio']
import httpx
import json
import pathlib

BASE_URL = "http://127.0.0.1:8000"
TEST_DATA_DIR = pathlib.Path(__file__).parent / "test_data"

@pytest.fixture
def async_client():
    """Provides an async HTTP client for FastAPI testing."""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

@pytest.fixture
def load_test_data():
    """Helper to load JSON test payloads."""
    def _load(filename):
        path = TEST_DATA_DIR / filename
        with open(path, 'r') as f:
            return json.load(f)
    return _load