# app/routes.py
from flask import Blueprint, request, jsonify, current_app as app
from .models import db, Department, Job, Employee
import pandas as pd
import sqlalchemy.exc
from sqlalchemy.exc import IntegrityError, OperationalError
from pandas.testing import assert_frame_equal
from sqlalchemy import text
import psycopg2
import logging
from .utils import pluralize, pluralize_columns, process_csv_employee
import os
from datetime import datetime
import numpy as np

bp = Blueprint("routes", __name__)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


S3_BUCKET = os.getenv("S3_BUCKET", "csv-api-employee-db")
LOCAL_CSV_PATH = os.getenv("LOCAL_CSV_PATH", "csv_files")
FLASK_ENV = os.getenv("FLASK_ENV", "testing")


def run_integration_tests(source):
    results_list = []
    file_csv_name = ["departments", "jobs", "hired_employees"]
    for csv_file in file_csv_name:
        model = pluralize(csv_file)
        logger.info(f"csv_file_name {csv_file}, model {model}")
        with app.app_context():
            query = db.session.query(model).statement
            db_df = pd.read_sql(query, db.engine)

            if source == "s3":
                file_path = f"s3://{S3_BUCKET}/csv_files/{csv_file}.csv"
            else:
                file_path = f"{LOCAL_CSV_PATH}/{csv_file}.csv"
            column_names = pluralize_columns(csv_file)
            csv_df = pd.read_csv(file_path, delimiter=",", names=column_names)
            if model == Employee:
                csv_df = csv_df.reset_index()
                csv_df = process_csv_employee(csv_df)
                db_df["hire_date"] = pd.to_datetime(db_df["hire_date"])
                db_df["name"] = db_df["name"].apply(
                    lambda x: np.nan if pd.isna(x) or x.lower() == "nan" else x
                )
                csv_df["name"] = csv_df["name"].apply(
                    lambda x: np.nan if pd.isna(x) or x.lower() == "nan" else x
                )
                db_df = db_df.replace(["", "null"], [np.nan, np.nan])
            else:
                csv_df.loc[len(csv_df)] = [len(csv_df) + 1, "not known"]
            try:
                assert_frame_equal(db_df, csv_df)
                message = f"Los DataFrames del modelo {model} son iguales."
                logger.info(message)
                results_list.append({"message": message, "status": 200})
            except AssertionError as e:
                message = (
                    f"Los DataFrames del modelo {model} son diferentes. Detalles: {e}"
                )
                logger.info(message)
                results_list.append({"message": message, "status": 400})
    return results_list


@bp.route("/run_integration_tests", methods=["GET"])
def run_tests():
    source = request.args.get("source")
    if FLASK_ENV != "testing":
        return jsonify({"error": "Endpoint only available in testing environment"}), 403
    test_results = run_integration_tests(source)
    return jsonify(test_results), 200


@bp.route("/upload_csv", methods=["POST"])
def upload_csv():
    logger.info("request: %s", request)
    file_value = request.args.get("file")
    source = request.args.get("source")
    logger.info("file value: %s", file_value)
    logger.info("source: %s", source)

    if not file_value or not any(
        x in file_value for x in ["departments", "jobs", "employees"]
    ):
        return (
            jsonify(
                {
                    "error": "El nombre del archivo no es válido. Debe contener 'departments', 'jobs' o 'employees'."
                }
            ),
            400,
        )

    if source == "s3":
        file_path = f"s3://{S3_BUCKET}/csv_files/{file_value}.csv"
    else:
        file_path = f"{LOCAL_CSV_PATH}/{file_value}.csv"

    if "departments" in file_value:
        df = pd.read_csv(file_path, delimiter=",", names=["id", "title"])
        df.loc[len(df)] = [-1, "not known"]
        logger.info("Loading rows: %s", df.shape)
        for _, row in df.iterrows():
            department = Department(name=row["title"])
            db.session.add(department)
    elif "jobs" in file_value:
        df = pd.read_csv(file_path, delimiter=",", names=["id", "title"])
        df.loc[len(df)] = [-1, "not known"]
        logger.info("Loading rows: %s", df.shape)
        for _, row in df.iterrows():
            job = Job(title=row["title"])
            db.session.add(job)
    elif "employees" in file_value:
        df = pd.read_csv(
            file_path,
            delimiter=",",
            names=["name", "hire_date", "department_id", "job_id"],
        )
        df = process_csv_employee(df)
        print("Loading rows: ", df.shape)
        for _, row in df.iterrows():
            employee = Employee(
                name=row["name"],
                job_id=row["job_id"],
                department_id=row["department_id"],
                hire_date=row["hire_date"],
            )
            db.session.add(employee)

    try:
        db.session.commit()
        logger.info(f"File {file_value} uploaded successfully")
        return jsonify({"message": f"File {file_value} uploaded successfully"}), 200
    except IntegrityError as e:
        error_message = str(e)
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": f"There is information that has been inserted already, the unique key contraint in the table {file_value} doens't allow to insert the same key",
                    "detail": error_message,
                }
            ),
            400,
        )

    except sqlalchemy.exc.ProgrammingError as e:
        db.session.rollback()
        return (
            jsonify({"error": f"You must create the tables in the database first {e}"}),
            400,
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/generate_report1", methods=["GET"])
def generate_report1():
    logger.info("Generating report")
    sql_query = """
    WITH hired_employees AS (
        SELECT
            e.id AS employee_id,
            e.name AS employee_name,
            e.hire_date,
            e.department_id,
            e.job_id,
            EXTRACT(quarter FROM e.hire_date) AS quarter
        FROM employee e
        WHERE EXTRACT(year FROM e.hire_date) = 2021
    ),
    job_names AS (
        SELECT
            j.id AS job_id,
            j.title AS job_name
        FROM job j
    ),
    department_names AS (
        SELECT
            d.id AS department_id,
            d.name AS department_name
        FROM department d
    )
    SELECT
        dn.department_name AS department,
        jn.job_name AS job,
	COUNT(CASE WHEN he.quarter = 1 THEN he.employee_id END) AS Q1,
    COUNT(CASE WHEN he.quarter = 2 THEN he.employee_id END) AS Q2,
    COUNT(CASE WHEN he.quarter = 3 THEN he.employee_id END) AS Q3,
    COUNT(CASE WHEN he.quarter = 4 THEN he.employee_id END) AS Q4
    FROM hired_employees he
    JOIN job_names jn ON he.job_id = jn.job_id
    JOIN department_names dn ON he.department_id = dn.department_id
    GROUP BY dn.department_name, jn.job_name, he.quarter
    ORDER BY dn.department_name, jn.job_name;
    """

    try:
        result = db.session.execute(text(sql_query))
        logger.info("Generating result %s", result)
        report_data = []
        for row in result:
            report_data.append(
                {
                    "department": row[0],
                    "job": row[1],
                    "Q1": row[2],
                    "Q2": row[3],
                    "Q3": row[4],
                    "Q4": row[5],
                }
            )

        return jsonify(report_data), 200
    except OperationalError as e:
        db.session.rollback()
        logger.error("Error conecting to sqlite %s", e)
        return jsonify({"error": f"Database operation error: {str(e)}"}), 200
    except sqlalchemy.exc.ProgrammingError as e:
        db.session.rollback()
        return (
            jsonify({"error": f"You must create the tables in the database first {e}"}),
            400,
        )
    except Exception as e:
        logger.error(f"Error: {type(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/generate_report2", methods=["GET"])
def generate_report2():
    print("Generating report")
    sql_query = """
    with count_hires_department as (
    SELECT
            d.id AS department_id,
            d.name AS department,
            COUNT(e.id) AS hired,
        AVG(COUNT(e.id)) OVER () AS mean_hires_by_dept
        FROM
            department d
        JOIN
            employee e ON d.id = e.department_id
        WHERE
            EXTRACT(YEAR FROM e.hire_date) = 2021
        GROUP BY
            d.id, d.name)

    select department_id, department,hired
    from count_hires_department as count_hires
    where mean_hires_by_dept < hired
    ;
    """
    try:
        result = db.session.execute(text(sql_query))
        logger.info("Generating result %s", result)
        report_data = []
        for row in result:
            report_data.append({"id": row[0], "deparment": row[1], "hired": row[2]})
        return jsonify(report_data), 200
    except OperationalError as e:
        db.session.rollback()
        logger.error("Error conecting to sqlite %s", e)
        return jsonify({"error": f"Database operation error: {str(e)}"}), 200
    except sqlalchemy.exc.ProgrammingError as e:
        db.session.rollback()
        return (
            jsonify({"error": f"You must create the tables in the database first {e}"}),
            400,
        )
    except Exception as e:
        logger.error(f"Error: {type(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/recreate_tables", methods=["DELETE"])
def recreate_tables():
    try:
        logger.info("recreando las tablas de la BD")
        db.drop_all()
        db.create_all()
        return jsonify({"message": "Tables recreated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/create_tables", methods=["POST"])
def create_tables():
    try:
        logger.info("creando las tablas de la BD")
        db.create_all()
        return jsonify({"message": "Tables created successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def null_report():
    results_list = []
    file_csv_name = ["departments", "jobs", "hired_employees"]
    for csv_file in file_csv_name:
        model = pluralize(csv_file)
        logger.info(f"csv_file_name {csv_file}, model {model}")
        with app.app_context():
            query = db.session.query(model).statement
            db_df = pd.read_sql(query, db.engine)
            if model == Employee:
                db_df["hire_date"] = pd.to_datetime(db_df["hire_date"])
                db_df["name"] = db_df["name"].apply(
                    lambda x: np.nan if pd.isna(x) or x.lower() == "nan" else x
                )
                db_df = db_df.replace(["", "null"], [np.nan, np.nan])
                max_job_id = db_df["job_id"].max()
                max_department_id = db_df["department_id"].max()
                max_hire_date = db_df["hire_date"].min()
                count_nulls_job_id = db_df["job_id"].value_counts().get(max_job_id, 0)
                count_nulls_hire_date = (
                    db_df["job_id"].value_counts().get(max_job_id, 0)
                )
                count_nulls_department_id = (
                    db_df["department_id"].value_counts().get(max_department_id, 0)
                )
                nan_count_name = db_df["name"].isna().sum()
                results_list.append(
                    {
                        "count_nulls_job_id": f"valor por defecto en la BD:{max_job_id}  conteo: {int(count_nulls_job_id)}",
                        "count_nulls_department_id": f"valor por defecto en la BD: {max_department_id} conteo: {int(count_nulls_department_id)}",
                        "nan_count_name": int(nan_count_name),
                        "nan_hire_date": f"valor por defecto en BD {max_hire_date} conteo: {int(count_nulls_hire_date)}",
                        "table": "Employees",
                    }
                )
            elif model == Department:
                db_df = db_df[db_df["name"] == "not known"]
                json_result = db_df.to_json(orient="records")
                results_list.append({"message": json_result, "table": "Department"})
            else:
                db_df = db_df[db_df["title"] == "not known"]
                json_result = db_df.to_json(orient="records")
                results_list.append({"message": json_result, "table": "Job"})

    return results_list


@bp.route("/run_null_report", methods=["GET"])
def run_null_report():
    if FLASK_ENV != "testing":
        return jsonify({"error": "Endpoint only available in testing environment"}), 403
    test_results = null_report()
    print(test_results)
    return jsonify(test_results), 200
