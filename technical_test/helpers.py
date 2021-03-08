import base64
import hashlib
import logging
import os
import random
import re
import sys
import typing

import bson
import flask
import pymongo

from technical_test import errors

EMAIL_REGEX = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
PASSWORD_MIN_LENGTH = 8


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    logger.setLevel(logging.INFO)

    return logger


LOG = get_logger(__name__)


def init_config(app: flask.Flask, config: dict = None, root_dir: str = None):
    if config:
        app.config.from_mapping(config)
        return

    settings_path = os.environ.get('APP_SETTINGS')
    if settings_path:
        if root_dir:
            settings_path = os.path.join(root_dir, settings_path)
        app.config.from_json(settings_path)
    else:
        raise RuntimeError('env var APP_SETTINGS is not set')


def get_config():
    if flask.current_app:
        return flask.current_app.config


class BaseClientError(errors.BaseError):
    pass


class MissingIdError(errors.BaseError):
    pass


class BaseClient:
    _client = None
    _db = None

    def __init__(self, uri: str, db_name: str):
        self._init_connection(uri, db_name)

    def _init_connection(self, uri: str, db_name: str):
        raise NotImplementedError()

    def insert(self, item_type: str, item_data: dict) -> str:
        raise NotImplementedError()

    def update(self, item_type: str, item_data: dict) -> bool:
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class MongoClient(BaseClient):

    def _init_connection(self, uri: str, db_name: str) -> None:
        self._client = pymongo.MongoClient(uri)
        self._db = self._client[db_name]

    def insert(self, item_type: str, item_data: dict) -> str:
        prepared_data = self._prepare_data(item_data)
        return str(self._get_collection(item_type).insert_one(prepared_data).inserted_id)

    def update(self, item_type: str, item_data: dict) -> bool:
        prepared_data = self._prepare_data(item_data)
        item_id = prepared_data.pop('_id', None)
        if not item_id:
            raise MissingIdError('Missing id when try to update this item type={item_type} data={item_data}')
        query = dict(_id=item_id)
        return self._get_collection(item_type).update_one(query, {'$set': prepared_data}).modified_count == 1

    def get(self, item_type: str, query: dict) -> typing.Optional[dict]:
        data = self._get_collection(item_type).find_one(self._prepare_data(query))
        if data:
            return self._return_data(data)

    def _prepare_data(self, query: dict) -> dict:
        return {
            f'_{key}' if key == 'id' else key: bson.ObjectId(value) if key == 'id' else value
            for key, value in query.items()
        }

    def _return_data(self, data: dict) -> dict:
        return {
            'id' if key == '_id' else key: str(value) if key == '_id' else value
            for key, value in data.items()
        }

    def _get_collection(self, collection_name: str) -> pymongo.collection.Collection:
        return self._db.get_collection(collection_name)

    def close(self):
        self._client.close()


def get_db_client(app: flask.Flask = None) -> BaseClient:
    if not app:
        app = flask.current_app

    if 'db_client' not in flask.g:
        flask.g.db_client = MongoClient(
            app.config.get('MONGO_URI'), app.config.get('MONGO_DB')
        )
    return flask.g.db_client


def init_db(app: flask.Flask) -> None:
    get_db_client(app)

    @app.teardown_appcontext
    def teardown_db(exception):
        db = flask.g.pop('db_client', None)
        if db is not None:
            db.close()


def get_validation_code() -> int:
    return random.randint(1000, 9999)


def send_email(receiver: str, subject: str, message: str) -> None:
    LOG.info(f'Send an email to {receiver} with subject "{subject}" and message "{message}"')


def is_email(email: str) -> bool:
    return bool(re.search(EMAIL_REGEX, email))


def check_email(email: str) -> None:
    if not is_email(email):
        raise errors.EmailError(email)


def check_password(password: str) -> None:
    if not password:
        raise errors.PasswordError('Password is required')

    if len(password) < PASSWORD_MIN_LENGTH:
        raise errors.PasswordError('Password must have 8 characters minimum')


def error_handler(ex):
    def make_response(ex: errors.BaseError, status_code: int):
        resp_json = {
            'message': ex.message
        }
        if hasattr(ex, 'error_type'):
            resp_json['error_type'] = ex.error_type
        resp = flask.jsonify(**resp_json)
        return resp, status_code

    try:
        raise ex
    except (errors.EmailError, errors.PasswordError, errors.ExistingUserEmailError, errors.InvalidPasswordError,
            errors.InvalidValidationCodeError, errors.InvalidEmailError):
        return make_response(ex, 400)
    except (errors.ExpiredValidationCodeError,):
        return make_response(ex, 403)
    except:
        flask.abort(500)


def hash_password(password: str, secret_key: str, salt: str = None) -> typing.Tuple[str, str]:
    if not salt:
        encoded_salt = os.urandom(32)
        salt = base64.b64encode(encoded_salt).decode('utf-8')

    salted_key = secret_key + salt
    encoded_salted_key = base64.b64decode(salted_key.encode('utf-8'))

    hashed_password = base64.b64encode(
        hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), encoded_salted_key, 100000)
    ).decode('utf-8')
    return hashed_password, salt
