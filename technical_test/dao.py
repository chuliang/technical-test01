import typing

from technical_test import helpers, models, errors


class BaseDaoError(errors.BaseError):
    pass


class UnexpectedFieldsError(BaseDaoError):

    def __init__(self, fields, unexpected_fields):
        super().__init__(f'{unexpected_fields} are not in model fields ({fields})')


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

    def get(self, **query) -> typing.Optional[models.BaseModel]:
        fields = self.model.fields()
        unexpected_fields = set(query) - {field.name for field in fields}
        if unexpected_fields:
            raise UnexpectedFieldsError(fields, unexpected_fields)

        data = self._client.get(self.entity_type, query)
        if data:
            return self.model(**data)


class User(BaseDao):
    entity_type = 'users'
    model = models.User

    def get(self, **query) -> typing.Optional[models.User]:
        return super().get(**query)
