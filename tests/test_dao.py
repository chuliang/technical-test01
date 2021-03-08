from datetime import datetime, timezone
from unittest import mock

import pytest

from technical_test import dao, models


def test_base_dao():
    mocked_client = mock.Mock()

    with pytest.raises(RuntimeError):
        dao.BaseDao(mocked_client)


def test_user_dao():
    mocked_client = mock.Mock()

    user_dao = dao.User(mocked_client)

    assert user_dao.entity_type == 'users'
    assert user_dao.model == models.User


def test_user_dao_insert():
    mocked_client = mock.Mock()
    user_dao = dao.User(mocked_client)
    user = models.User(email='email@email.fr', password='password')
    expected_id = 'expected_id'
    mocked_client.insert.return_value = expected_id

    updated_user = user_dao.insert(user)

    mocked_client.insert.assert_called_with(user_dao.entity_type, user.as_dict())
    assert updated_user.id == expected_id
    assert user.id == None


def test_user_dao_update():
    mocked_client = mock.Mock()
    user_dao = dao.User(mocked_client)
    user = models.User(
        email='email@email.fr', password='password', id='expected_id', validation_code=1234,
        validation_code_generated_at=datetime.now(timezone.utc)
    )

    updated_user = user_dao.update(user)

    mocked_client.update.assert_called_with(user_dao.entity_type, user.as_dict())
    for field_name in ('id', 'email', 'password', 'validation_code', 'validation_code_generated_at'):
        assert getattr(updated_user, field_name) == getattr(user, field_name)
    assert user is not updated_user
