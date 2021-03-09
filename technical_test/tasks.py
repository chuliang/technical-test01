from datetime import datetime, timezone

from technical_test import helpers, models, dao

LOG = helpers.get_logger(__name__)


class SendValidationCodeEmailTask(helpers.BaseTask):
    name = 'send_confirmation_code_email'

    def push(self, user: models.User):
        self.queue_client.push_task(self.name, dict(user_id=user.id))

    def run(self, user_id: str):
        user_dao = dao.User(self.db_client)
        user = user_dao.get(id=user_id)

        validation_code = helpers.get_validation_code()
        user = user.mutate(validation_code=validation_code, validation_code_generated_at=datetime.now(timezone.utc))
        try:
            helpers.send_email(receiver=user.email, subject='Welcome!', message=f'Your code: {validation_code}')
        except BaseException as e:
            # manage third party error
            # connection error
            # bad query
            LOG.error('Cannot send the email')
            raise e

        user_dao.update(user)
        return user

