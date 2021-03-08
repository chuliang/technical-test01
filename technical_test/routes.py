import flask

from technical_test import core

blueprint = flask.Blueprint('routes', __name__)


@blueprint.route('/health', methods=['GET'])
def index():
    message = flask.current_app.config.get('HEALTHY_MESSAGE')
    return message, 200


@blueprint.route('/users', methods=['POST'])
def create_user():
    json_data = flask.request.get_json()

    user = core.create_user(json_data.get('email'), json_data.get('password'))

    return user.as_response(), 200


@blueprint.route('/users/validation', methods=['POST'])
def check_validation_code():
    json_data = flask.request.get_json()

    user = core.check_validation_code(
        email=flask.request.authorization["username"],
        password=flask.request.authorization["password"],
        validation_code=json_data.get('validation_code')
    )

    return user.as_response(), 200
