import typing

from technical_test import helpers, models


class BaseDao:
    _client: helpers.BaseClient
    entity_type: str
    model: typing.Type[models.BaseModel]

    def __init__(self, client: helpers.BaseClient):
        if not hasattr(self, 'entity_type'):
            raise RuntimeError('entity_type must be filled')
        if not hasattr(self, 'model'):
            raise RuntimeError('model must be filled')

        self._client = client

    def insert(self, model_instance: models.BaseModel) -> models.BaseModel:
        user_id = self._client.insert(self.entity_type, model_instance.as_dict())
        return model_instance.mutate(id=user_id)

    def update(self, model_instance: models.BaseModel) -> models.User:
        self._client.update(self.entity_type, model_instance.as_dict())
        return model_instance.mutate()


class User(BaseDao):
    entity_type = 'users'
    model = models.User
