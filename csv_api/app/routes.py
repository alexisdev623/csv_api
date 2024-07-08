# app/routes.py
from flask import Blueprint, request, jsonify
from .models import db, Department, Job, Employee
import pandas as pd
import sqlalchemy.exc 
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import text
import psycopg2
import logging
import os

bp = Blueprint("routes", __name__)



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


S3_BUCKET = os.getenv('S3_BUCKET', 'csv-api-employee-db')
LOCAL_CSV_PATH = os.getenv('LOCAL_CSV_PATH', 'csv_files')


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
                jsonify(
                    {"error": f"Debes crear primero las tablas en la BD {e}"}
                ),
                400,
            )
        except sqlalchemy.exc.ProgrammingError as e:
            db.session.rollback()
            return (
                jsonify(
                    {"error": f"Debes crear primero las tablas en la BD {e}"}
                ),
                400,
            )
        df["job_id"] = df["job_id"].fillna(nulls_job_id).astype(int)
        df["department_id"] = df["department_id"].fillna(nulls_deparment_id).astype(int)
        df["hire_date"] = pd.to_datetime(
            df["hire_date"].fillna(pd.Timestamp("1970-01-01"))
        )
        df["name"] = df["name"].astype(str)
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
        db.session.rollback()
        return (
            jsonify(
                {"error": f"Duplicate key value violates unique constraint with {e}"}
            ),
            400,
        )
    except sqlalchemy.exc.ProgrammingError as e:
        db.session.rollback()
        return (
            jsonify(
                {"error": f"Debes crear primero las tablas en la BD {e}"}
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Error: {type(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/generate_report1", methods=["POST"])
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
            jsonify(
                {"error": f"Debes crear primero las tablas en la BD {e}"}
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Error: {type(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/generate_report2", methods=["POST"])
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
            jsonify(
                {"error": f"Debes crear primero las tablas en la BD {e}"}
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Error: {type(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/recreate_tables', methods=['DELETE'])
def recreate_tables():
    try:
        logger.info("recreando las tablas de la BD")
        db.drop_all()
        db.create_all()
        return jsonify({"message": "Tables recreated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/create_tables', methods=['POST'])
def create_tables():
    try:
        logger.info("creando las tablas de la BD")
        db.create_all()
        return jsonify({"message": "Tables created successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
