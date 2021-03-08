from unittest import mock

import pytest

import technical_test


@pytest.fixture
def config():
    return {
        'TESTING': True,
        'HEALTHY_MESSAGE': 'it works!',
        'SECRET_KEY': 'SECRET_KEY'
    }


@pytest.fixture
def app(config):
    with mock.patch.object(technical_test.helpers, 'init_db'):
        app = technical_test.create_app(config)
        yield app
