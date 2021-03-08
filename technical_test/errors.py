

class BaseError(Exception):
    error_type: str

    def __init__(self, message):
        self.message = message


class EmailError(BaseError):
    error_type = 'email_error'

    def __init__(self, email):
        super().__init__(f'{email} is not an email')


class PasswordError(BaseError):
    error_type = 'password_error'
