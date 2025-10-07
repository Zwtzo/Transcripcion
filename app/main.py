from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from contextlib import asynccontextmanager
from . import services
import json
import subprocess
import tempfile
import shutil
import os

# Importamos las librerías necesarias de FastAPI, WebSocket, y las herramientas de Python
# para manejar archivos temporales, procesos externos (FFmpeg) y la lógica de Vosk.

# Context manager 'lifespan' para manejar el inicio y apagado de la aplicación.
# Se asegura de que el modelo de Vosk se cargue una sola vez al inicio del servidor.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Código que se ejecuta al iniciar ---
    print("Cargando modelo de Vosk para la aplicación...")
    # Llamamos a la función que carga el modelo de Vosk (definida en 'services').
    services.load_vosk_model()
    print("Modelo de Vosk cargado exitosamente.")
    yield # Aquí el servidor está listo para recibir peticiones.
    # --- Código que se ejecuta al apagar (si fuera necesario) ---
    print("Aplicación finalizada.")

# Creamos la instancia principal de la aplicación FastAPI, usando el gestor de ciclo de vida.
app = FastAPI(lifespan=lifespan)

# Endpoint de verificación simple (GET /)
@app.get("/")
async def root():
    return {"message": "Servidor de transcripción funcionando"}

# ----------------------------------------------------------------------
## Endpoint REST para Transcripción de Archivos (/transcribe)
# ----------------------------------------------------------------------

@app.post("/transcribe")
async def transcribe_file(file: UploadFile = File(...)):
    # 1. GUARDAR ARCHIVO TEMPORALMENTE
    # Creamos un archivo temporal para guardar el archivo subido por el usuario.
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input_file:
        # Copiamos el contenido del archivo subido al archivo temporal.
        shutil.copyfileobj(file.file, temp_input_file)
        temp_input_path = temp_input_file.name
    
    # Definimos la ruta para el archivo de salida en formato PCM (raw audio).
    temp_output_path = temp_input_path + ".pcm"

    try:
        # 2. CONVERTIR AUDIO CON FFmpeg
        # Construimos el comando para FFmpeg: toma cualquier formato (-i) y lo convierte
        # a PCM (s16le), con 16kHz de frecuencia de muestreo (-ar) y mono (-ac 1).
        ffmpeg_command = [
            "ffmpeg", "-i", temp_input_path, "-f", "s16le",
            "-ar", "16000", "-ac", "1", temp_output_path
        ]
        # Ejecutamos FFmpeg. 'check=True' asegura que si falla, salte al 'except'.
        subprocess.run(ffmpeg_command, check=True, capture_output=True)

        # 3. TRANSCRIBIR CON VOSK
        with open(temp_output_path, "rb") as pcm_file:
            audio_data = pcm_file.read()
            # Inicializamos el reconocedor de Vosk con el modelo cargado.
            recognizer = services.KaldiRecognizer(services.VOSK_MODEL, 16000)
            # Procesamos la onda de audio completa.
            recognizer.AcceptWaveform(audio_data)
            # Obtenemos el resultado final como JSON y lo cargamos.
            result = json.loads(recognizer.FinalResult())
            # Devolvemos solo el texto de la transcripción.
            return {"text": result.get("text", "")}

    except subprocess.CalledProcessError as e:
        # Manejo de error si FFmpeg falla durante la conversión.
        return {"error": "Failed to convert audio file", "details": e.stderr.decode()}
    finally:
        # 4. LIMPIEZA
        # Aseguramos que los archivos temporales se eliminen, independientemente del resultado.
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

# ----------------------------------------------------------------------
## Endpoint WebSocket para Transcripción en Tiempo Real (/ws/transcribe)
# ----------------------------------------------------------------------

@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    # Aceptamos la conexión WebSocket entrante.
    await websocket.accept()
    recognizer = None
    try:
        # 1. ESPERAR HANDSHAKE DE INICIO
        # Esperamos el primer mensaje (debe ser JSON) con la configuración inicial (ej. sample_rate).
        handshake = await websocket.receive_json()
        
        # --- MANEJO DE ERRORES DE PROTOCOLO ---
        if handshake.get("type") != "start":
            # Si el cliente no envía el mensaje 'start' primero, es un error de protocolo.
            await websocket.send_json({
                "type": "error",
                "message": "Invalid handshake. First message must be of type 'start'."
            })
            # Cerramos la conexión con código 1008 (Violación de Política).
            await websocket.close(code=1008)
            return
        # ----------------------------------------
        
        sample_rate = handshake.get("sample_rate", 16000)
        # Inicializamos el reconocedor de Vosk para esta conexión específica.
        recognizer = services.KaldiRecognizer(services.VOSK_MODEL, sample_rate)

        # 2. BUCLE PRINCIPAL DE RECEPCIÓN DE DATOS (Stream)
        while True:
            # Esperamos recibir un mensaje del cliente (puede ser bytes de audio o texto JSON).
            message = await websocket.receive()
            
            if "bytes" in message:
                # Si es audio (bytes), lo enviamos al reconocedor de Vosk.
                if recognizer.AcceptWaveform(message["bytes"]):
                    # Si Vosk reconoce una frase completa, enviamos el resultado 'final'.
                    result = json.loads(recognizer.Result())
                    await websocket.send_json({"type": "final", "text": result.get("text", "")})
                else:
                    # Si no ha reconocido una frase completa, enviamos un resultado 'partial' (parcial).
                    partial_result = json.loads(recognizer.PartialResult())
                    await websocket.send_json({"type": "partial", "text": partial_result.get("partial", "")})
            
            elif "text" in message:
                # Si es un mensaje de texto (JSON).
                data = json.loads(message["text"])
                if data.get("type") == "eof":
                    # Si el cliente envía 'eof' (End Of File), forzamos el último resultado final de Vosk.
                    final_result = json.loads(recognizer.FinalResult())
                    await websocket.send_json({"type": "final", "text": final_result.get("text", "")})
                    break # Salimos del bucle para cerrar la conexión.

    except WebSocketDisconnect:
        # Manejo de la desconexión normal o abrupta por parte del cliente.
        print("Cliente desconectado.")
        # Intentamos obtener y enviar el resultado final, por si la desconexión fue inesperada.
        if recognizer:
            final_result = json.loads(recognizer.FinalResult())
            if final_result.get("text"):
                try:
                    await websocket.send_json({"type": "final", "text": final_result.get("text", "")})
                except Exception:
                    pass # Evitamos que un error de envío cause otro error.
    except Exception as e:
        # Manejo de cualquier otra excepción inesperada.
        print(f"Ocurrió un error inesperado: {e}")
        try:
            # Enviamos un mensaje de error genérico al cliente.
            await websocket.send_json({
                "type": "error",
                "message": f"Internal server error: {e}"
            })
        except Exception:
            pass
    finally:
        # 3. CIERRE
        # Aseguramos que la conexión se cierre al finalizar (tanto si hay éxito como error).
        await websocket.close()