import os

import flask


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
