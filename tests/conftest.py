import pytest

from technical_test import create_app


@pytest.fixture
def config():
    return {
        'TESTING': True,
        'HEALTHY_MESSAGE': 'it works!'
    }


@pytest.fixture
def app(config):
    app = create_app(config)
    yield app
