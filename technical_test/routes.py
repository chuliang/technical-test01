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
