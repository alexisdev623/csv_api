# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
DATABASE_URL = os.getenv('DATABASE_URL')

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        DATABASE_URL
    )
    db.init_app(app)
    Migrate(app, db)
    from . import routes

    app.register_blueprint(routes.bp)
    return app
