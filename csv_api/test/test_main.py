# tests/test_routes.py
import os
import tempfile
import pytest
from flask import Flask
from app.routes import bp
from app.models import db, Department, Job, Employee


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["TESTING"] = True

    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Setup initial data for tests
        db.session.add(Department())
        db.session.add(Job())
        db.session.add(Employee())
        # db.session.commit()

    app.register_blueprint(bp)

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


def test_upload_csv_departments(client):
    data = {"file": "departments"}
    response = client.post("/upload_csv", query_string=data)
    assert response.status_code == 200
    assert response.json == {"message": "File uploaded successfully"}


def test_upload_csv_jobs(client):
    data = {"file": "jobs"}
    response = client.post("/upload_csv", query_string=data)
    assert response.status_code == 200
    assert response.json == {"message": "File uploaded successfully"}


def test_upload_csv_employees(client):
    data = {"file": "hired_employees"}
    response = client.post("/upload_csv", query_string=data)
    assert response.status_code == 200
    assert response.json == {"message": "File uploaded successfully"}


def test_generate_report1(client):
    response = client.post("/generate_report1")
    assert response.status_code == 200


def test_generate_report2(client):
    response = client.post("/generate_report2")
    assert response.status_code == 200
