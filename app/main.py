from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from . import services
import json
import subprocess
import tempfile
import shutil

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Esta función se ejecuta cuando la aplicación inicia."""
    services.load_vosk_model()

@app.get("/")
async def root():
    """Endpoint de prueba para verificar que el servidor está funcionando."""
    return {"message": "Servidor de transcripción funcionando"}

# --- NUEVO CÓDIGO AQUÍ ---
@app.post("/transcribe")
async def transcribe_file(file: UploadFile = File(...)):
    """
    Recibe un archivo de audio, lo convierte y devuelve la transcripción.
    """
    # 1. Guarda el archivo subido en una ubicación temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_input_file:
        shutil.copyfileobj(file.file, temp_input_file)
        temp_input_path = temp_input_file.name

    # 2. Prepara la ruta para el archivo de salida convertido (PCM)
    temp_output_path = temp_input_path + ".pcm"

    try:
        # 3. Construye y ejecuta el comando de FFmpeg para la conversión
        ffmpeg_command = [
            "ffmpeg",
            "-i", temp_input_path,    # Archivo de entrada
            "-f", "s16le",            # Formato PCM 16-bit little-endian
            "-ar", "16000",           # Frecuencia de muestreo 16kHz
            "-ac", "1",               # 1 canal (mono)
            temp_output_path          # Archivo de salida
        ]
        subprocess.run(ffmpeg_command, check=True, capture_output=True)

        # 4. Lee el audio convertido y lo transcribe con Vosk
        with open(temp_output_path, "rb") as pcm_file:
            audio_data = pcm_file.read()
            
            recognizer = services.KaldiRecognizer(services.VOSK_MODEL, 16000)
            recognizer.AcceptWaveform(audio_data)
            result = json.loads(recognizer.FinalResult())
            
            return {"text": result.get("text", "")}

    except subprocess.CalledProcessError as e:
        # Si FFmpeg falla, devuelve un error
        return {"error": "Failed to convert audio file", "details": e.stderr.decode()}
    finally:
        # 5. Limpia los archivos temporales
        import os
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

# --- FIN DEL NUEVO CÓDIGO ---

@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    # (El código del WebSocket que ya tenías va aquí, sin cambios)
    await websocket.accept()
    
    try:
        # 1. Esperar y validar el handshake JSON del cliente
        handshake = await websocket.receive_json()
        if handshake.get("type") != "start":
            await websocket.close(code=1008, reason="Invalid handshake")
            return
        
        recognizer = services.KaldiRecognizer(services.VOSK_MODEL, handshake.get("sample_rate", 16000))

        # 2. Bucle principal para recibir datos
        while True:
            # Esperamos recibir datos, que pueden ser audio (bytes) o un mensaje de texto (str)
            message = await websocket.receive()

            # Verificamos si el mensaje contiene audio
            if isinstance(message.get("bytes"), bytes):
                audio_chunk = message["bytes"]
                if recognizer.AcceptWaveform(audio_chunk):
                    result = json.loads(recognizer.Result())
                    await websocket.send_json({"type": "final", "text": result.get("text", "")})
                else:
                    partial_result = json.loads(recognizer.PartialResult())
                    await websocket.send_json({"type": "partial", "text": partial_result.get("partial", "")})
            
            # Verificamos si es un mensaje de texto (para el "eof")
            elif isinstance(message.get("text"), str):
                data = json.loads(message["text"])
                if data.get("type") == "eof":
                    # El cliente indicó que terminó, enviamos el resultado final y salimos del bucle
                    final_result = json.loads(recognizer.FinalResult())
                    await websocket.send_json({"type": "final", "text": final_result.get("text", "")})
                    break # Salir del bucle while para cerrar la conexión

    except WebSocketDisconnect:
        print("Cliente desconectado.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        # Aseguramos que la conexión se cierre al finalizar
        await websocket.close()

