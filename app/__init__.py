import os

from flask import Flask, g
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_uploads import configure_uploads, patch_request_class
from flask_wtf.csrf import CSRFProtect
from flask_moment import Moment

from .decorators import no_cache, rate_limit
from .models import db, login_manager

bootstrap = Bootstrap()
csrf = CSRFProtect()
migrate = Migrate()
moment = Moment()


def create_app(config_name):
    """Create an application instance."""
    app = Flask(__name__)

    # apply configuration
    cfg = os.path.join(os.getcwd(), 'config', config_name + '.py')
    app.config.from_pyfile(cfg)
    app.config['UPLOADS_DEFAULT_DEST'] = os.path.join(os.getcwd(), 'uploads')

    # initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)

    # register blueprints
    from .api_v1 import v1_api as api
    app.register_blueprint(api, url_prefix='/api/v1')

    from .public_blueprint import login_api
    app.register_blueprint(login_api, url_prefix='/auth')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .api_v1 import images as image_object
    configure_uploads(app, (image_object, ))
    patch_request_class(app, size=150 * 1024)  # 150KB max

    csrf.exempt(api)
    csrf.exempt(login_api)

    # register an after request handler
    @app.after_request
    def after_request(rv):
        headers = getattr(g, 'headers', {})
        rv.headers.extend(headers)
        return rv

    return app
