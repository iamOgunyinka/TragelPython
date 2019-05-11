import os
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from .decorators import json, no_cache, rate_limit

db = SQLAlchemy()


def create_app(config_name):
    """Create an application instance."""
    app = Flask(__name__)

    # apply configuration
    cfg = os.path.join(os.getcwd(), 'config', config_name + '.py')
    app.config.from_pyfile(cfg)

    # initialize extensions
    db.init_app(app)

    # register blueprints
    from .api_v1 import v1_api as api
    app.register_blueprint(api, url_prefix='/api/v1')

    from .login_blueprint import login_api as lapi
    app.register_blueprint(lapi, url_prefix='/auth')

    # register an after request handler
    @app.after_request
    def after_request(rv):
        headers = getattr(g, 'headers', {})
        rv.headers.extend(headers)
        return rv

    return app
