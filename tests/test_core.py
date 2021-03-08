from datetime import datetime, timezone
from unittest import mock

from technical_test import core


def test_create_user():
    email = 'email@email.fr'
    password = 'password'
    expected_id = 'expected_id'
    expected_validation_code = 1234
    expected_validation_code_generated_at = datetime.now(timezone.utc)
    with mock.patch.object(core, 'helpers') as mocked_helpers, mock.patch.object(core, 'datetime') as mocked_datetime:
        mocked_db_client = mocked_helpers.get_db_client.return_value
        mocked_db_client.insert.return_value = expected_id
        mocked_helpers.get_validation_code.return_value = expected_validation_code
        mocked_datetime.now.return_value = expected_validation_code_generated_at

        user = core.create_user(email, password)

    assert user.email == email
    assert user.password == password
    assert user.id == expected_id
    assert user.validation_code == expected_validation_code
    assert user.validation_code_generated_at == expected_validation_code_generated_at
