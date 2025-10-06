# 1. Imagen base: Empezamos con una imagen oficial de Python 3.9 ligera.
FROM python:3.9-slim

# 2. Instalar ffmpeg: Actualizamos los paquetes e instalamos ffmpeg.
RUN apt-get update && apt-get install -y ffmpeg

# 3. Directorio de trabajo: Creamos una carpeta /code dentro del contenedor
#    y la establecemos como nuestro directorio de trabajo.
WORKDIR /code

# 4. Instalar dependencias: Copiamos primero el archivo de requisitos
#    y luego instalamos las librerías. Esto aprovecha la caché de Docker.
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Copiar el código y el modelo: Copiamos nuestra carpeta 'app' y 'model'
#    al directorio de trabajo /code dentro del contenedor.
COPY ./app /code/app
COPY ./model /code/model

# 6. Exponer el puerto: Le decimos a Docker que la aplicación escuchará
#    en el puerto 8000.
EXPOSE 8000

# 7. Comando de inicio: Este es el comando que se ejecutará cuando
#    el contenedor arranque. Inicia el servidor uvicorn.
#    --host 0.0.0.0 es crucial para que sea accesible desde fuera del contenedor.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
