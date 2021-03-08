import dataclasses
from datetime import datetime


@dataclasses.dataclass(frozen=True)
class BaseModel:

    def as_dict(self):
        return dataclasses.asdict(self)

    def mutate(self, **changes):
        return dataclasses.replace(self, **changes)

    def as_response(self):
        """
        Use it to create a response with exposed fields
        To exposed a field, assign this `dataclasses.field(metadata=dict(exposed=True))`
        """
        return {
            field.name: getattr(self, field.name)
            for field in dataclasses.fields(self)
            if field.metadata.get('exposed')
        }

    @classmethod
    def fields(self):
        return dataclasses.fields(self)


@dataclasses.dataclass(frozen=True)
class User(BaseModel):
    email: str = dataclasses.field(metadata=dict(exposed=True))
    password: str
    salt: str
    id: str = dataclasses.field(default=None, metadata=dict(exposed=True))
    validation_code: int = None
    validation_code_generated_at: datetime = None
