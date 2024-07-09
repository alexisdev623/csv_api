# app/models.py
from . import db


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False, unique=True)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"), nullable=True)
    hire_date = db.Column(db.DateTime, nullable=True)
