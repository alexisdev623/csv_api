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
Copiar código
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

URL: /upload_csv
Método: POST
Descripción: Este endpoint permite cargar datos desde un archivo CSV a la base de datos.

Parámetros:

file: Nombre del archivo CSV (debe contener departments, jobs o hired_employees).
source: Fuente del archivo (local o s3).
Ejemplo:

```bash
Copiar código

curl -X POST "http://127.0.0.1:5000/upload_csv?file=departments&source=local"
```


Generar Reporte 1
URL: /generate_report1
Método: POST
Descripción: Genera un reporte de contrataciones por trimestre para cada departamento y trabajo en el año 2021.

Ejemplo:

```bash
Copiar código

curl -X POST "http://127.0.0.1:5000/generate_report1"
```


Generar Reporte 2
URL: /generate_report2
Método: POST
Descripción: Genera un reporte de departamentos que contrataron más empleados que el promedio en el año 2021.

Ejemplo:

```bash
Copiar código

curl -X POST "http://127.0.0.1:5000/generate_report2"
```





## Estructura del Proyecto
```
Copiar código
├── app/
│   ├── __init__.py
│   ├── models.py
│   └── routes.py
├── csv_files/
│   ├── departments.csv
│   ├── jobs.csv
│   └── employees.csv
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
Asegúrate de que los archivos CSV estén correctamente formateados y que los nombres de los archivos contengan departments, jobs o hired_employees.
Para los archivos de departments y jobs, se añade una fila adicional con un valor por defecto "not known" para manejar datos nulos.
Para el archivo de employees, las columnas department_id y job_id se rellenan con valores nulos si es necesario, y la columna hire_date se establece en una fecha predeterminada si falta.
