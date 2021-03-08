from unittest import mock

from technical_test import core


def test_create_user():
    email = 'email@email.fr'
    password = 'password'
    expected_id = 'expected_id'
    with mock.patch.object(core, 'helpers') as mocked_helpers:
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_db_client.insert.return_value = expected_id

        user = core.create_user(email, password)

    assert user.email == email
    assert user.password == password
    assert user.id == expected_id
