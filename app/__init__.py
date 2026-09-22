import os
from datetime import timedelta

from flask import Flask
from dotenv import load_dotenv

from app.database.db import db

# Load variables from .env
load_dotenv()


def create_app():

    app = Flask(__name__)

    # =====================================================
    # BASIC CONFIGURATION
    # =====================================================

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "pavesense-development-secret-key"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pavesense.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Remember Me session duration
    app.permanent_session_lifetime = timedelta(
        days=30
    )

    # =====================================================
    # UPLOAD FOLDER
    # =====================================================

    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.root_path,
        "static",
        "uploads"
    )

    # =====================================================
    # DATABASE
    # =====================================================

    db.init_app(app)

    # =====================================================
    # GOOGLE OAUTH CONFIGURATION
    # =====================================================

    app.config["GOOGLE_CLIENT_ID"] = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    app.config["GOOGLE_CLIENT_SECRET"] = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    # =====================================================
    # GOOGLE OAUTH INITIALIZATION
    # =====================================================

    from app.routes.auth import auth, oauth

    oauth.init_app(app)

    # =====================================================
    # BLUEPRINTS
    # =====================================================

    from app.routes.home import home
    from app.routes.complaint import complaint
    from app.routes.dashboard import dashboard
    from app.routes.profile import profile

    app.register_blueprint(home)
    app.register_blueprint(auth)
    app.register_blueprint(complaint)
    app.register_blueprint(dashboard)
    app.register_blueprint(profile)

    # =====================================================
    # CREATE DATABASE TABLES
    # =====================================================

    with app.app_context():
        db.create_all()

    return app