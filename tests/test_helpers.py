from unittest import mock

import bson
import pytest

from technical_test import helpers


def test_base_client():
    uri = 'uri'
    db_name = 'db_name'

    with pytest.raises(NotImplementedError):
        helpers.BaseDbClient(uri, db_name)


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


def test_mongo_client_update():
    uri = 'uri'
    db_name = 'db_name'
    entity_type = 'entity_type'
    _id = bson.ObjectId()
    data = dict(data='data', id=str(_id))
    expected_filter = dict(_id=_id)
    expected_query = {'$set': dict(data='data')}
    with mock.patch.object(helpers, 'pymongo') as mocked_pymongo:
        mocked_mongo_client = mocked_pymongo.MongoClient.return_value
        mocked_db = mocked_mongo_client[db_name]
        mocked_collection = mocked_db.get_collection.return_value
        mongo_client = helpers.MongoClient(uri, db_name)

        mongo_client.update(entity_type, data)

        mocked_db.get_collection.assert_called_with(entity_type)
        mocked_collection.update_one.assert_called_with(expected_filter, expected_query)


def test_mongo_client_update_without_id():
    uri = 'uri'
    db_name = 'db_name'
    entity_type = 'entity_type'
    data = dict(data='data')
    with pytest.raises(helpers.MissingIdError):
        mongo_client = helpers.MongoClient(uri, db_name)

        mongo_client.update(entity_type, data)


def test_mongo_client_get():
    uri = 'uri'
    db_name = 'db_name'
    entity_type = 'entity_type'
    _id = bson.ObjectId()
    query = dict(id=str(_id))
    expected_query = dict(_id=_id)
    with mock.patch.object(helpers, 'pymongo') as mocked_pymongo:
        mocked_mongo_client = mocked_pymongo.MongoClient.return_value
        mocked_db = mocked_mongo_client[db_name]
        mocked_collection = mocked_db.get_collection.return_value
        mongo_client = helpers.MongoClient(uri, db_name)

        mongo_client.get(entity_type, query)

        mocked_db.get_collection.assert_called_with(entity_type)
        mocked_collection.find_one.assert_called_with(expected_query)


def test_hash_password():
    password = 'password'
    secret_key = 'secret_key'
    hashed_password, salt = helpers.hash_password(password, secret_key)

    hashed_password_again_with_same_salt, same_salt = helpers.hash_password(password, secret_key, salt)

    assert salt == same_salt
    assert hashed_password == hashed_password_again_with_same_salt


def test_hash_password_changed_secret_key():
    password = 'password'
    secret_key = 'secret_key'
    hashed_password, salt = helpers.hash_password(password, secret_key)
    new_secret_key = 'new_secret_key'

    hashed_password_again_with_same_salt, same_salt = helpers.hash_password(password, new_secret_key, salt)

    assert salt == same_salt
    assert hashed_password != hashed_password_again_with_same_salt


def test_hash_password_changed_secret_key():
    password = 'password'
    secret_key = 'secret_key'
    hashed_password, salt = helpers.hash_password(password, secret_key)

    new_salt = 'new_salt'
    hashed_password_again_with_new_salt, new_returned_salt = helpers.hash_password(password, secret_key, new_salt)

    assert new_salt == new_returned_salt
    assert salt != new_returned_salt
    assert hashed_password != hashed_password_again_with_new_salt
