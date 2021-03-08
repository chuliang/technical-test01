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
