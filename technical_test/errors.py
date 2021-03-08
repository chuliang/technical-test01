

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


class ExistingUserEmailError(BaseError):
    error_type = 'existing_user_email_error'


class ExpiredValidationCodeError(BaseError):
    error_type = 'expired_validation_code_error'

    def __init__(self):
        super().__init__('Your code expired')


class InvalidValidationCodeError(BaseError):
    error_type = 'invalid_validation_code_error'

    def __init__(self):
        super().__init__('Your code is invalid')


class InvalidPasswordError(BaseError):
    error_type = 'invalid_password_error'

    def __init__(self):
        super().__init__('Your password is invalid')


class InvalidEmailError(BaseError):
    error_type = 'invalid_email_error'

    def __init__(self):
        super().__init__('Your email is invalid')

