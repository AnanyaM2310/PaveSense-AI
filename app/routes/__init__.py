from flask import Flask
from config import Config

from app.routes.home import home
from app.routes.complaint import complaint

def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    app.config.from_object(Config)

    # Register Blueprints
    app.register_blueprint(home)
    app.register_blueprint(complaint)

    return app