from datetime import datetime, timezone

from technical_test import dao, helpers, models, errors
from technical_test.helpers import get_logger, send_email

LOG = get_logger(__name__)


def create_user(email, password):
    helpers.check_email(email)
    helpers.check_password(password)

    user_dao = dao.User(helpers.get_db_client())
    existing_user = user_dao.get(email=email)
    if existing_user:
        raise errors.ExistingUserEmailError(email)

    user = models.User(
        email=email,
        password=password
    )
    user = user_dao.insert(user)

    LOG.info(f'user created {user.id}')

    user = send_confirmation_code_email(user)

    return user


def send_confirmation_code_email(user):
    validation_code = helpers.get_validation_code()
    send_email(receiver=user.email, subject='Welcome!', message=f'Your code: {validation_code}')

    user_dao = dao.User(helpers.get_db_client())
    user = user.mutate(validation_code=validation_code, validation_code_generated_at=datetime.now(timezone.utc))
    user_dao.update(user)
    return user
