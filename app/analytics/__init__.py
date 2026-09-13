from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os

from app.database.models import db, User


# Load environment variables
load_dotenv()


login_manager = LoginManager()


def create_app():

    app = Flask(__name__)

    # =====================================================
    # CONFIGURATION
    # =====================================================

    app.config['SECRET_KEY'] = os.getenv(
        'SECRET_KEY',
        'dev-secret-key'
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:password@localhost/subscription_app'
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    # =====================================================
    # INITIALIZE DATABASE
    # =====================================================

    db.init_app(app)


    # =====================================================
    # INITIALIZE LOGIN MANAGER
    # =====================================================

    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'


    # =====================================================
    # USER LOADER
    # =====================================================

    @login_manager.user_loader
    def load_user(user_id):

        return User.query.get(int(user_id))


    # =====================================================
    # REGISTER BLUEPRINTS
    # =====================================================

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.subscriptions.routes import subscriptions_bp
    from app.analytics.routes import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(analytics_bp)


    # =====================================================
    # CREATE DATABASE TABLES
    # =====================================================

    with app.app_context():
        db.create_all()


    return app