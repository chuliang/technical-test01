import flask


blueprint = flask.Blueprint('routes', __name__)


@blueprint.route('/health', methods=['GET'])
def index():
    message = flask.current_app.config.get('HEALTHY_MESSAGE')
    return message, 200
