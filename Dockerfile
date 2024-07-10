# Usa una imagen base de Python
FROM python:3.11

# Establece el directorio de trabajo
WORKDIR /csv_api

COPY . .

# Copia los archivos de requisitos
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Expon el puerto que usará Flask
EXPOSE 5000

# Establecer el entorno de Flask
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0

# Comando para ejecutar la aplicación
CMD ["flask", "run"]
