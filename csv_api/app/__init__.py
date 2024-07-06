# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localdb/employee'
    db.init_app(app)
    migrate = Migrate(app, db)
    from . import routes
    app.register_blueprint(routes.bp)
    return app
