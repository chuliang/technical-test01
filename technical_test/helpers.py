import base64
import functools
import hashlib
import json
import logging
import os
import random
import re
import sys
import typing

import bson
import flask
import pika
import pymongo

from technical_test import errors

EMAIL_REGEX = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
PASSWORD_MIN_LENGTH = 8
CACHED_CONFIG = None
# ../
ROOT_DIR =  os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


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

    global CACHED_CONFIG
    if CACHED_CONFIG:
        return CACHED_CONFIG

    settings_path = os.environ.get('APP_SETTINGS')
    if not settings_path:
        raise RuntimeError('env var APP_SETTINGS is not set')

    with open(os.path.join(ROOT_DIR, settings_path)) as f:
        CACHED_CONFIG = json.load(f)
    return CACHED_CONFIG


class BaseClientError(errors.BaseError):
    pass


class MissingIdError(errors.BaseError):
    pass


class BaseDbClient:
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


class BaseQueueClient:
    _connection = None
    _channel = None
    _queue_name: str
    _db_client: BaseDbClient
    # cannot use BaseTask before the declaration, and BaseTask uses BaseClient >-<
    #_registered_tasks: typing.Dict[str, typing.Type[BaseTask]]
    _registered_tasks: typing.Dict[str, typing.Type]

    def __init__(self, uri: str, queue_name: str, db_client: BaseDbClient):
        self._create_connection(uri, queue_name)
        self._registered_tasks = {}
        self._db_client = db_client

    def _create_connection(self, uri: str, queue_name: str):
        raise NotImplementedError()

    def push_task(self, task_name: str, task_kwargs: dict):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class MongoClient(BaseDbClient):

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
        options = bson.CodecOptions(tz_aware=True)
        return self._db.get_collection(collection_name, codec_options=options)

    def close(self):
        self._client.close()


def get_db_client(cached=True) -> BaseDbClient:

    def _get_client():
        config = get_config()
        LOG.info(f'_get_client')
        return MongoClient(
            config.get('MONGO_URI'), config.get('MONGO_DB')
        )

    if not flask.current_app or not cached:
        return _get_client()

    if 'db_client' not in flask.g:
        flask.g.db_client = _get_client()
    return flask.g.db_client


def get_queue_client(cached: bool = False, db_client: BaseDbClient = None) -> BaseQueueClient:
    if not db_client:
        db_client = get_db_client()

    def _get_client():
        config = get_config()
        return RabbitClient(
            config.get('RABBIT_URI'), config.get('RABBIT_QUEUE'), db_client
        )

    if not flask.current_app or not cached:
        return _get_client()

    if 'queue_client' not in flask.g:
        flask.g.queue_client = _get_client()
    return flask.g.queue_client


def init_db(app: flask.Flask) -> None:

    @app.teardown_appcontext
    def teardown_db(exception):
        db_client = flask.g.pop('db_client', None)
        if db_client is not None:
            db_client.close()


def init_queue(app: flask.Flask) -> None:

    @app.teardown_appcontext
    def teardown_db(exception):
        queue_client = flask.g.pop('queue_client', None)
        if queue_client is not None:
            queue_client.close()


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


class BaseTask:
    name: str

    def __init__(self, queue_client: BaseDbClient = None, db_client: BaseDbClient = None):
        self._queue_client = queue_client
        self._db_client = db_client

    @property
    def queue_client(self) -> BaseQueueClient:
        if not self._queue_client:
            self._queue_client = get_queue_client()
        return self._queue_client

    @property
    def db_client(self) -> BaseDbClient:
        if not self._db_client:
            self._db_client = get_db_client()
        return self._db_client


class RabbitClient(BaseQueueClient):
    _connection: pika.BlockingConnection
    _channel = pika.adapters.blocking_connection.BlockingChannel

    def _create_connection(self, uri: str, queue_name: str):
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(uri))
        self._channel = self._connection.channel()
        self._queue_name = queue_name
        self._channel.queue_declare(queue=self._queue_name)

    def push_task(self, task_name: str, task_kwargs: dict):
        self._channel.basic_publish(
            exchange='',
            routing_key=self._queue_name,
            body=json.dumps(dict(task_name=task_name, task_kwargs=task_kwargs))
        )

    def listen(self):

        def ack_message(channel, delivery_tag):
            if channel.is_open:
                channel.basic_ack(delivery_tag)

        def callback(ch, method, properties, body):
            LOG.info(f'receive {body}')
            deserialized_body = json.loads(body)
            self.pop_task(deserialized_body.get('task_name'), deserialized_body.get('task_kwargs'))

            cb = functools.partial(ack_message, self._channel, method.delivery_tag)
            self._connection.add_callback_threadsafe(cb)

        self._channel.basic_consume(queue=self._queue_name, on_message_callback=callback)
        self._channel.start_consuming()

    def pop_task(self, task_name: str, task_kwargs: dict):
        task = self._registered_tasks[task_name](self, self._db_client)
        task.run(**task_kwargs)

    def register_task(self, task: BaseTask):
        self._registered_tasks[task.name] = task

    def close(self):
        self._connection.close()
