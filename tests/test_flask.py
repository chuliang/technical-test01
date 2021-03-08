from unittest import mock


def test_health(app, config):
    test_client = app.test_client()

    resp = test_client.get('/health')

    assert resp.status_code == 200
    assert resp.data.decode('utf-8') == config.get('HEALTHY_MESSAGE')


def test_create_user(app):
    test_client = app.test_client()
    payload = dict(email='email@email.fr', password='password')
    expected_id = 'expected_id'
    with mock.patch('technical_test.core.helpers') as mocked_helpers:
        mocked_db_client = mocked_helpers.get_db_client.return_value
        # get a user with this email -> None
        mocked_db_client.get.return_value = None
        mocked_db_client.insert.return_value = 'expected_id'

        resp = test_client.post('/users', json=payload)

    assert resp.status_code == 200
    assert resp.json.get('email') == payload.get('email')
    assert resp.json.get('id') == expected_id
    assert resp.json.get('validation_code') is None
    assert resp.json.get('validation_code_generated_at') is None
    assert resp.json.get('password') is None


def test_create_user_with_wrong_email(app):
    test_client = app.test_client()
    payload = dict(email='emailemail.fr', password='password')

    resp = test_client.post('/users', json=payload)

    assert resp.status_code == 400
    assert resp.json.get('error_type') == 'email_error'


def test_create_user_with_shorten_password(app):
    test_client = app.test_client()
    payload = dict(email='email@email.fr', password='pass')

    resp = test_client.post('/users', json=payload)

    assert resp.status_code == 400
    assert resp.json.get('error_type') == 'password_error'


def test_create_user_with_existing_email(app):
    test_client = app.test_client()
    payload = dict(email='email@email.fr', password='password')
    expected_id = 'expected_id'
    with mock.patch('technical_test.core.helpers') as mocked_helpers:
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_db_client.get.return_value = dict(email=payload['email'], password='sdfsfdf')

        resp = test_client.post('/users', json=payload)

    assert resp.status_code == 400
    assert resp.json.get('error_type') == 'existing_user_email_error'

