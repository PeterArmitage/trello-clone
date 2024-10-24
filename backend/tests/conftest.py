import pytest
from app.main import app

@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    app.state.testing = True