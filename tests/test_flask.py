import base64
from datetime import datetime, timezone, timedelta
from unittest import mock

import bson


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
        mocked_helpers.hash_password.return_value = ('hashed_password', 'salt')
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
        mocked_db_client.get.return_value = dict(email=payload['email'], password='sdfsfdf', salt='salt')

        resp = test_client.post('/users', json=payload)

    assert resp.status_code == 400
    assert resp.json.get('error_type') == 'existing_user_email_error'


def test_check_validation_code(app):
    test_client = app.test_client()
    user_id = str(bson.ObjectId())
    email = 'email@email.fr'
    hashed_password = 'hashed_password'
    salt = 'salt'
    validation_code = 1234
    validation_code_generated_at = datetime.now(timezone.utc)
    credentials = base64.b64encode(b'email@email.fr:test_password').decode('utf-8')
    headers = {
        'Authorization': f'Basic {credentials}'
    }
    payload = dict(validation_code=validation_code)
    with mock.patch('technical_test.core.helpers') as mocked_helpers, \
            mock.patch('technical_test.core.datetime') as mocked_datetime:
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_helpers.hash_password.return_value = ('hashed_password', 'salt')
        mocked_datetime.now.return_value = validation_code_generated_at + timedelta(seconds=30)
        mocked_db_client.get.return_value = dict(
            email=email, password=hashed_password, salt=salt, validation_code=validation_code, id=user_id,
            validation_code_generated_at=validation_code_generated_at
        )

        resp = test_client.post('/users/validation', json=payload, headers=headers)

    assert resp.status_code == 200
    assert resp.json.get('email') == email
    assert resp.json.get('id') == user_id
    assert resp.json.get('is_valid')


def test_check_validation_code_expired_code(app):
    test_client = app.test_client()
    user_id = str(bson.ObjectId())
    email = 'email@email.fr'
    hashed_password = 'hashed_password'
    salt = 'salt'
    validation_code = 1234
    validation_code_generated_at = datetime.now(timezone.utc)
    credentials = base64.b64encode(b'email@email.fr:test_password').decode('utf-8')
    headers = {
        'Authorization': f'Basic {credentials}'
    }
    payload = dict(validation_code=validation_code)
    with mock.patch('technical_test.core.helpers') as mocked_helpers, \
            mock.patch('technical_test.core.datetime') as mocked_datetime:
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_helpers.hash_password.return_value = ('hashed_password', 'salt')
        mocked_datetime.now.return_value = validation_code_generated_at + timedelta(minutes=2)
        mocked_db_client.get.return_value = dict(
            email=email, password=hashed_password, salt=salt, validation_code=validation_code, id=user_id,
            validation_code_generated_at=validation_code_generated_at
        )

        resp = test_client.post('/users/validation', json=payload, headers=headers)

    assert resp.status_code == 403
    assert resp.json.get('error_type') == 'expired_validation_code_error'


