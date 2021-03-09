import os

import flask

from technical_test import helpers, errors

# ../
ROOT_DIR =  os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def create_app(config: dict = None):
    app = flask.Flask(__name__)

    helpers.init_config(app, config, ROOT_DIR)
    with app.app_context():
        helpers.init_db(app)
        helpers.init_queue(app)

    from technical_test.routes import blueprint
    app.register_blueprint(blueprint)
    app.register_error_handler(errors.BaseError, helpers.error_handler)

    return app
