# tests/test_routes.py
import os
import tempfile
import pytest
from flask import Flask
from app.routes import bp
from app.models import db, Department, Job, Employee
import boto3
from moto import mock_aws
from datetime import date


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["TESTING"] = True

    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.add(Department(name="test"))
        db.session.add(Job(title="test"))
        db.session.add(Employee(name="test", hire_date=date(2023, 1, 1)))
        db.session.commit()

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
    assert response.json == {"message": "File departments uploaded successfully"}


def test_upload_csv_jobs(client):
    data = {"file": "jobs"}
    response = client.post("/upload_csv", query_string=data)
    assert response.status_code == 200
    assert response.json == {"message": "File jobs uploaded successfully"}


def test_upload_csv_employees(client):
    data = {"file": "hired_employees"}
    response = client.post("/upload_csv", query_string=data)
    assert response.status_code == 200
    assert response.json == {"message": "File hired_employees uploaded successfully"}


def test_generate_report1(client):
    response = client.get("/generate_report1")
    assert response.status_code == 200


def test_generate_report2(client):
    response = client.get("/generate_report2")
    assert response.status_code == 200


def test_create_tables(client):
    response = client.post("/create_tables")
    assert response.status_code == 200


@mock_aws
def test_upload_csv_departments_from_s3(client):
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket_name = "csv-api-employee-db"
    s3.create_bucket(Bucket=bucket_name)
    s3.upload_file(
        "csv_files/departments.csv", bucket_name, "csv_files/departments.csv"
    )
    data = {"file": "departments", "source": "s3"}
    response = client.post("/upload_csv", query_string=data)
    assert response.status_code == 200
    assert response.json == {"message": "File departments uploaded successfully"}


@mock_aws
def test_upload_csv_jobs_from_s3(client):
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket_name = "csv-api-employee-db"
    s3.create_bucket(Bucket=bucket_name)
    s3.upload_file("csv_files/jobs.csv", bucket_name, "csv_files/jobs.csv")
    data = {"file": "jobs", "source": "s3"}
    response = client.post("/upload_csv", query_string=data)
    assert response.status_code == 200
    assert response.json == {"message": "File jobs uploaded successfully"}


@mock_aws
def test_upload_csv_hired_employees_from_s3(client):
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket_name = "csv-api-employee-db"
    s3.create_bucket(Bucket=bucket_name)
    s3.upload_file(
        "csv_files/hired_employees.csv", bucket_name, "csv_files/hired_employees.csv"
    )
    data = {"file": "hired_employees", "source": "s3"}
    response = client.post("/upload_csv", query_string=data)
    assert response.status_code == 200
    assert response.json == {"message": "File hired_employees uploaded successfully"}
