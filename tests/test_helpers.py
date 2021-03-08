from unittest import mock

import bson
import pytest

from technical_test import helpers


def test_base_client():
    uri = 'uri'
    db_name = 'db_name'

    with pytest.raises(NotImplementedError):
        helpers.BaseClient(uri, db_name)


def test_mongo_client():
    uri = 'uri'
    db_name = 'db_name'
    with mock.patch.object(helpers, 'pymongo') as mocked_pymongo:
        mocked_mongo_client = mocked_pymongo.MongoClient.return_value

        mongo_client = helpers.MongoClient(uri, db_name)

        mocked_pymongo.MongoClient.assert_called_with(uri)
        assert mocked_mongo_client[db_name] == mongo_client._db


def test_mongo_client_insert():
    uri = 'uri'
    db_name = 'db_name'
    entity_type = 'entity_type'
    _id = bson.ObjectId()
    data = dict(data='data', id=str(_id))
    expected_data = dict(data='data', _id=_id)
    with mock.patch.object(helpers, 'pymongo') as mocked_pymongo:
        mocked_mongo_client = mocked_pymongo.MongoClient.return_value
        mocked_db = mocked_mongo_client[db_name]
        mocked_collection = mocked_db.get_collection.return_value
        mongo_client = helpers.MongoClient(uri, db_name)

        mongo_client.insert(entity_type, data)

        mocked_db.get_collection.assert_called_with(entity_type)
        mocked_collection.insert_one.assert_called_with(expected_data)
