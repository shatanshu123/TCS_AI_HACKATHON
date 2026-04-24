from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.routes import api
from app.storage import init_db


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app)
    config_object.ensure_directories()
    init_db(app.config["DATABASE_PATH"])

    app.register_blueprint(api)
    return app

