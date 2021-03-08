from datetime import datetime, timezone, timedelta

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

    config = helpers.get_config()
    hashed_password, salt = helpers.hash_password(password, config.get('SECRET_KEY'))
    user = models.User(
        email=email,
        password=hashed_password,
        salt=salt
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


def check_validation_code(email, password, validation_code):
    config = helpers.get_config()
    user_dao = dao.User(helpers.get_db_client())
    user = user_dao.get(email=email)
    if not user:
        raise errors.InvalidEmailError()

    hashed_password, _ = helpers.hash_password(password, config.get('SECRET_KEY'), user.salt)
    if user.password != hashed_password:
        raise errors.InvalidPasswordError()

    if user.is_valid:
        return user

    if user.validation_code != validation_code:
        raise errors.InvalidValidationCodeError()

    if user.validation_code_generated_at + timedelta(minutes=1) < datetime.now(timezone.utc):
        raise errors.ExpiredValidationCodeError()

    user = user.mutate(is_valid=True)
    return user_dao.update(user)
