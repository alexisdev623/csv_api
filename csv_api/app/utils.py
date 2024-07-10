from datetime import datetime
import pandas as pd
import logging
import psycopg2
from flask import jsonify
import sqlalchemy.exc
import boto3
from .models import db, Department, Job, Employee

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pluralize(file):
    if file == "departments":
        return Department
    elif file == "jobs":
        return Job
    elif file == "hired_employees":
        return Employee


def pluralize_columns(file):
    if file == "departments":
        return ["id", "name"]
    elif file == "jobs":
        return ["id", "title"]
    elif file == "hired_employees":
        return ["name", "hire_date", "department_id", "job_id"]
    else:
        return 0


def process_csv_employee(csv_df):
    csv_df = csv_df.reset_index()
    csv_df = csv_df[["index", "name", "job_id", "department_id", "hire_date"]]
    csv_df = csv_df.rename(columns={"index": "id"})
    try:
        deparment_query = Department.query.filter_by(name="not known").all()
        job_query = Job.query.filter_by(title="not known").all()
        nulls_deparment_id = deparment_query[0].id
        nulls_job_id = job_query[0].id
    except IndexError:
        default_null_value = -1
        logger.error(
            f"No hay registrados nulos en deparment_id y en job_id, se asume: {default_null_value}"
        )
        nulls_deparment_id = default_null_value
        nulls_job_id = default_null_value
    except psycopg2.errors.UndefinedTable as e:
        db.session.rollback()
        return (
            jsonify({"error": f"You must create the tables in the database first {e}"}),
            400,
        )
    except sqlalchemy.exc.ProgrammingError as e:
        db.session.rollback()
        return (
            jsonify({"error": f"You must create the tables in the database first {e}"}),
            400,
        )
    csv_df["job_id"] = csv_df["job_id"].fillna(nulls_job_id).astype(int)

    csv_df["department_id"] = (
        csv_df["department_id"].fillna(nulls_deparment_id).astype(int)
    )

    csv_df["hire_date"] = pd.to_datetime(csv_df["hire_date"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    csv_df["hire_date"] = pd.to_datetime(
        csv_df["hire_date"].fillna(datetime(1970, 1, 1))
    )
    csv_df["hire_date"] = pd.to_datetime(csv_df["hire_date"])
    csv_df["name"] = csv_df["name"].astype(str)
    return csv_df

