from datetime import datetime, timezone, timedelta
from unittest import mock

import bson
import pytest

from technical_test import core, errors, tasks


def test_create_user(config):
    email = 'email@email.fr'
    password = 'password'
    hashed_password = 'hashed_password'
    salt = 'salt'
    expected_id = 'expected_id'
    with mock.patch.object(core, 'helpers') as mocked_helpers:
        mocked_helpers.hash_password.return_value = (hashed_password, salt)
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_queue_client = mocked_helpers.get_queue_client.return_value
        # get user with this email
        mocked_db_client.get.return_value = None
        mocked_db_client.insert.return_value = expected_id

        user = core.create_user(email, password)

    mocked_queue_client.push_task.assert_called_with(
        tasks.SendValidationCodeEmailTask.name, dict(user_id=expected_id)
    )
    assert user.email == email
    assert user.password != password
    assert user.password == hashed_password
    assert user.salt == salt
    assert user.id == expected_id


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
        mocked_db_client.get.return_value = dict(email=email, password='dddfgdg', salt='salt')

        core.create_user(email, password)


def test_check_validation_code(config):
    user_id = str(bson.ObjectId())
    email = 'email@email.fr'
    password = 'password'
    hashed_password = 'hashed_password'
    salt = 'salt'
    validation_code = 1234
    validation_code_generated_at = datetime.now(timezone.utc)

    with mock.patch.object(core, 'helpers') as mocked_helpers, mock.patch.object(core, 'datetime') as mocked_datetime:
        mocked_helpers.hash_password.return_value = (hashed_password, salt)
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_datetime.now.return_value = validation_code_generated_at + timedelta(seconds=30)
        mocked_db_client.get.return_value = dict(
            email=email, password=hashed_password, salt=salt, validation_code=validation_code, id=user_id,
            validation_code_generated_at=validation_code_generated_at
        )

        user = core.check_validation_code(email, password, validation_code)

    assert user.email == email
    assert user.password != password
    assert user.password == hashed_password
    assert user.salt == salt
    assert user.id == user_id
    assert user.is_valid


def test_check_validation_code_expired(config):
    user_id = str(bson.ObjectId())
    email = 'email@email.fr'
    password = 'password'
    hashed_password = 'hashed_password'
    salt = 'salt'
    validation_code = 1234
    validation_code_generated_at = datetime.now(timezone.utc)

    with mock.patch.object(core, 'helpers') as mocked_helpers, mock.patch.object(core, 'datetime') as mocked_datetime:
        mocked_helpers.hash_password.return_value = (hashed_password, salt)
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_datetime.now.return_value = validation_code_generated_at + timedelta(minutes=2)
        mocked_db_client.get.return_value = dict(
            email=email, password=hashed_password, salt=salt, validation_code=validation_code, id=user_id,
            validation_code_generated_at=validation_code_generated_at
        )

        with pytest.raises(errors.ExpiredValidationCodeError):
            core.check_validation_code(email, password, validation_code)


def test_check_validation_code_invalid(config):
    user_id = str(bson.ObjectId())
    email = 'email@email.fr'
    password = 'password'
    hashed_password = 'hashed_password'
    salt = 'salt'
    validation_code = 1234
    invalid_validation_code = 4567

    with mock.patch.object(core, 'helpers') as mocked_helpers:
        mocked_helpers.hash_password.return_value = (hashed_password, salt)
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_db_client.get.return_value = dict(
            email=email, password=hashed_password, salt=salt, validation_code=validation_code, id=user_id,
        )

        with pytest.raises(errors.InvalidValidationCodeError):
            core.check_validation_code(email, password, invalid_validation_code)


def test_check_validation_code_invalid_password(config):
    user_id = str(bson.ObjectId())
    email = 'email@email.fr'
    password = 'password'
    hashed_password = 'hashed_password'
    invalid_hashed_password = 'invliad_hashed_password'
    salt = 'salt'
    validation_code = 1234

    with mock.patch.object(core, 'helpers') as mocked_helpers:
        mocked_helpers.hash_password.return_value = (invalid_hashed_password, salt)
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_db_client.get.return_value = dict(
            email=email, password=hashed_password, salt=salt, validation_code=validation_code, id=user_id,
        )

        with pytest.raises(errors.InvalidPasswordError):
            core.check_validation_code(email, password, validation_code)


def test_check_validation_code_invalid_email(config):
    email = 'email@email.fr'
    password = 'password'
    validation_code = 1234

    with mock.patch.object(core, 'helpers') as mocked_helpers:
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_db_client.get.return_value = None

        with pytest.raises(errors.InvalidEmailError):
            core.check_validation_code(email, password, validation_code)
