from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from . import services
import json
import subprocess
import tempfile
import shutil
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación.
    Carga el modelo de Vosk al iniciar.
    """
    # Código que se ejecuta ANTES de que la aplicación empiece a aceptar peticiones
    print("Cargando modelo de Vosk para la aplicación...")
    services.load_vosk_model()
    yield
    # Código que se ejecuta DESPUÉS (no es necesario para este caso)
    print("Aplicación finalizada.")

# Se inicializa la app con el manejador de ciclo de vida "lifespan"
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    """Endpoint de prueba para verificar que el servidor está funcionando."""
    return {"message": "Servidor de transcripción funcionando"}

@app.post("/transcribe")
async def transcribe_file(file: UploadFile = File(...)):
    """Recibe un archivo de audio, lo convierte y devuelve la transcripción."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_input_file:
        shutil.copyfileobj(file.file, temp_input_file)
        temp_input_path = temp_input_file.name

    temp_output_path = temp_input_path + ".pcm"

    try:
        ffmpeg_command = ["ffmpeg", "-i", temp_input_path, "-f", "s16le", "-ar", "16000", "-ac", "1", temp_output_path]
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)

        with open(temp_output_path, "rb") as pcm_file:
            audio_data = pcm_file.read()
            recognizer = services.KaldiRecognizer(services.VOSK_MODEL, 16000)
            recognizer.AcceptWaveform(audio_data)
            result = json.loads(recognizer.FinalResult())
            return {"text": result.get("text", "")}

    except subprocess.CalledProcessError as e:
        return {"error": "Failed to convert audio file", "details": e.stderr}
    finally:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        handshake = await websocket.receive_json()
        if handshake.get("type") != "start":
            await websocket.close(code=1008, reason="Invalid handshake")
            return
        
        recognizer = services.KaldiRecognizer(services.VOSK_MODEL, handshake.get("sample_rate", 16000))

        while True:
            message = await websocket.receive()
            if "bytes" in message:
                if recognizer.AcceptWaveform(message["bytes"]):
                    result = json.loads(recognizer.Result())
                    await websocket.send_json({"type": "final", "text": result.get("text", "")})
                else:
                    partial_result = json.loads(recognizer.PartialResult())
                    await websocket.send_json({"type": "partial", "text": partial_result.get("partial", "")})
            
            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "eof":
                    final_result = json.loads(recognizer.FinalResult())
                    await websocket.send_json({"type": "final", "text": final_result.get("text", "")})
                    break
    except WebSocketDisconnect:
        print("Cliente desconectado.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        await websocket.close()

