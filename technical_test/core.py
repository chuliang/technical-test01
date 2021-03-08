from technical_test import dao, helpers, models
from technical_test.helpers import get_logger

LOG = get_logger(__name__)


def create_user(email, password):
    user_dao = dao.User(helpers.get_db_client())
    user = models.User(
        email=email,
        password=password
    )
    user = user_dao.insert(user)

    LOG.info(f'user created {user.id}')

    # send email

    return user