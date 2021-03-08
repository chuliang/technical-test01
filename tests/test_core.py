from datetime import datetime, timezone
from unittest import mock

import pytest

from technical_test import core, errors


def test_create_user():
    email = 'email@email.fr'
    password = 'password'
    expected_id = 'expected_id'
    expected_validation_code = 1234
    expected_validation_code_generated_at = datetime.now(timezone.utc)
    with mock.patch.object(core, 'helpers') as mocked_helpers, mock.patch.object(core, 'datetime') as mocked_datetime:
        mocked_db_client = mocked_helpers.get_db_client.return_value
        # get user with this email
        mocked_db_client.get.return_value = None
        mocked_db_client.insert.return_value = expected_id
        mocked_helpers.get_validation_code.return_value = expected_validation_code
        mocked_datetime.now.return_value = expected_validation_code_generated_at

        user = core.create_user(email, password)

    assert user.email == email
    assert user.password == password
    assert user.id == expected_id
    assert user.validation_code == expected_validation_code
    assert user.validation_code_generated_at == expected_validation_code_generated_at


def test_create_user_with_wrong_email():
    email = 'emailemail.fr'
    password = 'password'
    with pytest.raises(errors.EmailError):

        core.create_user(email, password)


def test_create_user_with_empty_email():
    email = ''
    password = 'password'
    with pytest.raises(errors.EmailError):

        core.create_user(email, password)


def test_create_user_with_shorten_password():
    email = 'email@email.fr'
    password = 'pass'
    with pytest.raises(errors.PasswordError):

        core.create_user(email, password)


def test_create_user_with_empty_password():
    email = 'email@email.fr'
    password = ''
    with pytest.raises(errors.PasswordError):

        core.create_user(email, password)


def test_create_user_with_existing_email():
    email = 'email@email.fr'
    password = 'password'
    with mock.patch.object(core, 'helpers') as mocked_helpers, pytest.raises(errors.ExistingUserEmailError):
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_db_client.get.return_value = dict(email=email, password='dddfgdg')

        core.create_user(email, password)
