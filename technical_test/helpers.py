import logging
import os
import sys

import bson
import flask
import pymongo


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


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    logger.setLevel(logging.INFO)

    return logger


class BaseClient:
    _client = None
    _db = None

    def __init__(self, uri: str, db_name: str):
        self._init_connection(uri, db_name)

    def _init_connection(self, uri: str, db_name: str):
        raise NotImplementedError()

    def insert(self, item_type: str, item_data: dict) -> str:
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class MongoClient(BaseClient):

    def _init_connection(self, uri: str, db_name: str):
        self._client = pymongo.MongoClient(uri)
        self._db = self._client[db_name]

    def insert(self, item_type: str, item_data: dict) -> str:
        prepared_data = self._prepare_data(item_data)
        return str(self._get_collection(item_type).insert_one(prepared_data).inserted_id)

    def _prepare_data(self, query: dict) -> dict:
        return {
            f'_{key}' if key == 'id' else key: bson.ObjectId(value) if key == 'id' else value
            for key, value in query.items()
        }

    def _get_collection(self, collection_name: str):
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


def init_db(app: flask.Flask):
    get_db_client(app)

    @app.teardown_appcontext
    def teardown_db(exception):
        db = flask.g.pop('db_client', None)
        if db is not None:
            db.close()
