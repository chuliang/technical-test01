from datetime import datetime, timezone
from unittest import mock

import bson
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
    user = models.User(email='email@email.fr', password='password', salt='salt')
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
        validation_code_generated_at=datetime.now(timezone.utc), salt='salt'
    )

    updated_user = user_dao.update(user)

    mocked_client.update.assert_called_with(user_dao.entity_type, user.as_dict())
    for field_name in ('id', 'email', 'password', 'validation_code', 'validation_code_generated_at'):
        assert getattr(updated_user, field_name) == getattr(user, field_name)
    assert user is not updated_user


def test_user_dao_get():
    mocked_client = mock.Mock()
    user_dao = dao.User(mocked_client)
    query = dict(id='id')
    expected_user = dict(
        id=str(bson.ObjectId()),
        email='email@email.fr',
        password='password',
        salt='salt'
    )
    mocked_client.get.return_value = expected_user

    updated_user = user_dao.get(**query)

    mocked_client.get.assert_called_with(user_dao.entity_type, query)
    for field_name in ('id', 'email', 'password'):
        assert getattr(updated_user, field_name) == expected_user.get(field_name)


def test_user_dao_get_with_unexpected_field():
    mocked_client = mock.Mock()
    user_dao = dao.User(mocked_client)
    query = dict(wtf='wtf')

    with pytest.raises(dao.UnexpectedFieldsError):
        user_dao.get(**query)

