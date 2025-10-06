# API de Transcripción en Tiempo Real con Vosk

Este proyecto es una API en Python construida con **FastAPI** que transcribe audio utilizando el motor de reconocimiento de voz offline **Vosk**. Ofrece dos modos de operación: transcripción en tiempo real a través de WebSockets y transcripción de archivos completos mediante un endpoint REST.

El proyecto está diseñado para ser modular, fácil de desplegar y está completamente containerizado con Docker.

## ✨ Características

-   **Transcripción en Tiempo Real (WebSocket)**: Envía un stream de audio y recibe transcripciones parciales y finales al instante.
-   **Transcripción de Archivos (REST API)**: Sube un archivo de audio completo (`.wav`, `.mp3`, etc.) y obtén la transcripción completa.
-   **Motor Offline**: El procesamiento se realiza localmente con Vosk, sin depender de servicios en la nube.
-   **Conversión de Formato**: Utiliza FFmpeg para normalizar automáticamente los archivos de audio al formato requerido.
-   **Pruebas Automatizadas**: Incluye pruebas con `pytest` que cubren los endpoints REST y WebSocket.
-   **Listo para Despliegue**: Incluye un `Dockerfile` y `docker-compose.yml` para una fácil ejecución.

---

## 🚀 Requisitos Previos

Para ejecutar este proyecto localmente, necesitarás:

-   Python 3.9+
-   FFmpeg
-   Docker Desktop

---

## 🔧 Instalación y Configuración Local

Sigue estos pasos para poner en marcha el proyecto en tu máquina.

### 1. Clona el Repositorio


git clone https://github.com/Zwtzo/Transcripci-n
cd Transcripci-n

### 2. Configura el Entorno de Python
Crea y activa un entorno virtual para aislar las dependencias.

# Crear el entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS/Linux
source venv/bin/activate
###  3. Instala las Dependencias
Instala las librerías de Python necesarias.
pip install -r requirements.txt

### 4. Descarga el Modelo de Vosk (ya incluido)
La aplicación requiere un modelo de Vosk para funcionar.

Descarga un modelo desde la página oficial de modelos de Vosk. Se recomienda un modelo pequeño para empezar, como vosk-model-small-es-0.42 para español.

Crea una carpeta llamada model en la raíz del proyecto.

Descomprime el archivo descargado y mueve su contenido a la carpeta model. La estructura final debe ser la siguiente:
/
|-- /model/
|   |-- /am/
|   |-- /conf/
|   |-- ... (y otros archivos del modelo)
|-- ... (resto de carpetas del proyecto)

### Cómo Ejecutar la Aplicación
# Ejecución Local
Con el entorno virtual activado, inicia el servidor desde la raíz del proyecto:
uvicorn app.main:app --reload
El servidor estará disponible en http://127.0.0.1:8000.

# Ejecución con Docker
Si tienes Docker instalado y corriendo, puedes usar los siguientes comandos.

docker build -t transcription-api .
docker run -p 8000:8000 transcription-api
El servidor estará disponible en http://localhost:8000.

# Ejemplos de Uso
Asegúrate de que el servidor (local o en Docker) esté corriendo.
Endpoint REST (/transcribe)
Usa curl en una terminal para subir un archivo de audio y recibir la transcripción completa.
curl -X POST "http://localhost:8000/transcribe" -F "file=@samples/1.wav"
Respuesta esperada:
JSON
{"text":"café con pan"}
Endpoint WebSocket (/ws/transcribe)

# transcipcion tiempo real
Para probar la transcripción en tiempo real, puedes usar el script client_test.py.
Prepara el audio: El cliente WebSocket necesita enviar el audio en formato PCM. Puedes convertir un archivo .wav usando FFmpeg:
ffmpeg -i samples/1.wav -f s16le -ar 16000 -ac 1 samples/1.pcm
Ejecuta el cliente de Python:
python client_test.py

La terminal del cliente mostrará los mensajes de transcripción partial y final enviados por el servidor.

# Cómo Correr los Tests
Para verificar que toda la API funciona correctamente, ejecuta las pruebas automatizadas con pytest.
pytest
El comando ejecutará todas las pruebas definidas en la carpeta tests/ y mostrará un resumen de los resultados.