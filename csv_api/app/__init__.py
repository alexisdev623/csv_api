# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import boto3

def get_parameter(parameter_name):
    ssm = boto3.client('ssm', region_name="us-east-1")
    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        parameter_value = response['Parameter']['Value']
        return parameter_value
    except ssm.exceptions.ParameterNotFound:
        print(f"Parameter {parameter_name} not found.")
        return None
    except Exception as e:
        print(f"Error retrieving parameter {parameter_name}: {e}")
        return None


db = SQLAlchemy()
parameter_name = "DATABASE_URL"
DATABASE_URL = get_parameter(parameter_name)


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    db.init_app(app)
    Migrate(app, db)
    from . import routes

    app.register_blueprint(routes.bp)
    return app
