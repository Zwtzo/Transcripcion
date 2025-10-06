from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from contextlib import asynccontextmanager
from . import services
import json
import subprocess
import tempfile
import shutil
import os

# Context manager 'lifespan' para manejar el inicio y apagado de la aplicación.
# Esta es la forma moderna y recomendada en FastAPI.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Código que se ejecuta al iniciar ---
    print("Cargando modelo de Vosk para la aplicación...")
    services.load_vosk_model()
    print("Modelo de Vosk cargado exitosamente.")
    yield
    # --- Código que se ejecuta al apagar (si fuera necesario) ---
    print("Aplicación finalizada.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Servidor de transcripción funcionando"}

@app.post("/transcribe")
async def transcribe_file(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input_file:
        shutil.copyfileobj(file.file, temp_input_file)
        temp_input_path = temp_input_file.name
    
    temp_output_path = temp_input_path + ".pcm"

    try:
        ffmpeg_command = [
            "ffmpeg", "-i", temp_input_path, "-f", "s16le",
            "-ar", "16000", "-ac", "1", temp_output_path
        ]
        subprocess.run(ffmpeg_command, check=True, capture_output=True)

        with open(temp_output_path, "rb") as pcm_file:
            audio_data = pcm_file.read()
            recognizer = services.KaldiRecognizer(services.VOSK_MODEL, 16000)
            recognizer.AcceptWaveform(audio_data)
            result = json.loads(recognizer.FinalResult())
            return {"text": result.get("text", "")}

    except subprocess.CalledProcessError as e:
        return {"error": "Failed to convert audio file", "details": e.stderr.decode()}
    finally:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    recognizer = None
    try:
        # 1. Esperar y validar el handshake
        handshake = await websocket.receive_json()
        
        # --- NUEVO CÓDIGO DE MANEJO DE ERRORES ---
        if handshake.get("type") != "start":
            # Si el handshake no es válido, enviamos un mensaje de error
            await websocket.send_json({
                "type": "error",
                "message": "Invalid handshake. First message must be of type 'start'."
            })
            # Y cerramos la conexión con un código de error de protocolo
            await websocket.close(code=1008)
            return
        # --- FIN DEL NUEVO CÓDIGO ---
        
        sample_rate = handshake.get("sample_rate", 16000)
        recognizer = services.KaldiRecognizer(services.VOSK_MODEL, sample_rate)

        # 2. Bucle principal para recibir datos
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
        # Opcional: si el cliente se desconecta abruptamente, aún podemos intentar enviar un resultado final
        if recognizer:
            final_result = json.loads(recognizer.FinalResult())
            if final_result.get("text"):
                # Este envío puede fallar si el socket ya está completamente cerrado, pero es un buen intento.
                try:
                    await websocket.send_json({"type": "final", "text": final_result.get("text", "")})
                except Exception:
                    pass # Ignoramos el error si no se puede enviar
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        # Enviar un mensaje de error genérico si ocurre una excepción no controlada
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Internal server error: {e}"
            })
        except Exception:
            pass # Ignoramos si no se puede enviar
    finally:
        # Aseguramos que la conexión se cierre al finalizar
        await websocket.close()

