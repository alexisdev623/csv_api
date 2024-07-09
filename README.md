# csv_api
CSV API for Employee Database

## Descripción

Esta es una aplicación web basada en Flask que permite la migración de datos de archivos CSV a una base de datos SQL y la generación de reportes específicos. La aplicación incluye endpoints para cargar datos de departments, jobs y employees, así como para generar reportes basados en los datos cargados.


## Requisitos previos:

Tener git
Tener docker y docker-compose instalados en el computador




## Instalación
Clonar el repositorio:

```
git clone https://github.com/alexisdev623/csv_api.git

cd csv_api
```

## Uso
Ejecutar la aplicación
Para ejecutar la aplicación localmente, solo debes usar el siguiente comando:
```
docker-compose up --build -d

```

### Configuración de la Base de datos
Esto solo se debe hacer en la primera ejecución
```
Crear las tablas en la BD

curl -X POST "http://127.0.0.1:5000/create_tables"
```


## Test de la API

Endpoints:
```
 * Running on http://127.0.0.1:5000
 * Running on http://172.18.0.2:5000
```

### Cargar csvs
URL: /upload_csv
Método: POST
Descripción: Este endpoint permite cargar datos desde un archivo CSV a la base de datos.

Parámetros:

file: Nombre del archivo CSV (debe contener departments, jobs o hired_employees).
source: Fuente del archivo (local o s3).
Ejemplo:

```bash

curl -X POST "http://127.0.0.1:5000/upload_csv?file=departments&source=local"
```

### crear las tablas
URL: /create_tables
Método: POST
Descripción: Crea las tablas en la BD

```bash

curl -X POST "http://127.0.0.1:5000/create_tables"
```

### Recrear las tablas
URL: /create_tables
Método: POST
Descripción: Borra y crea de nuevo las tablas en la BD

```bash

curl -X POST "http://127.0.0.1:5000/recreate_tables"
```


### Generar Reporte 1
URL: /generate_report1
Método: GET
Descripción: Genera un reporte de contrataciones por trimestre para cada departamento y trabajo en el año 2021.

Ejemplo:

```bash

curl -X GET "http://127.0.0.1:5000/generate_report1"
```


### Generar Reporte 2
URL: /generate_report2
Método: GET
Descripción: Genera un reporte de departamentos que contrataron más empleados que el promedio en el año 2021.

Ejemplo:

```bash

curl -X GET "http://127.0.0.1:5000/generate_report2"
```


### Generar Reporte de nulls
URL: /run_null_report
Método: GET
Descripción: Genera el reporte de nulos de las tablas

Ejemplo:

```bash

curl -X GET "http://127.0.0.1:5000/run_null_report"
```


### Ejecutar pruebas de integración
URL: /run_integration_tests
Método: GET
Descripción: Ejecuta las pruebas de integración que consiste en comparar los datos del csv con los datos que existen en la tabla de la BD.
La comparación de las dataframes se hace mediante assert_frame_equal(db_df, csv_df), lo cual garantiza que la información es 100% igual.

Ejemplo:

```bash

curl -X GET "http://127.0.0.1:5000/run_integration_tests"
```





## Estructura del Proyecto
```
├── app/
│   ├── __init__.py
│   ├── models.py
│   └── routes.py
├── csv_files/
│   ├── departments.csv
│   ├── jobs.csv
│   └── hired_employees.csv
├── venv/
├── config.py
├── requirements.txt
└── README.md
```

app/__init__.py: Inicializa la aplicación Flask y la base de datos.

app/models.py: Define los modelos de la base de datos (Department, Job, Employee).

app/routes.py: Define los endpoints de la API.

csv_files/: Directorio que contiene los archivos CSV.

config.py: Archivo de configuración para la aplicación.

requirements.txt: Lista de dependencias del proyecto.

README.md: Este archivo.



## Notas
Para los archivos de departments y jobs, se añade una fila adicional con un valor por defecto "not known" para manejar datos nulos.
Para el archivo de employees, las columnas department_id y job_id se rellenan con valores nulos si es necesario, y la columna hire_date se establece en una fecha predeterminada si falta.
