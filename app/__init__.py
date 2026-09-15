from flask import Flask, render_template
from flask_login import LoginManager
from dotenv import load_dotenv

from config import Config
from app.database.models import db, User, ensure_database_schema

load_dotenv()

login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.subscriptions.routes import subscriptions_bp
    from app.analytics.routes import analytics_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.errorhandler(401)
    def unauthorized(error):
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    with app.app_context():
        db.create_all()
        ensure_database_schema()

    return app