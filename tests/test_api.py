import pytest
from fastapi.testclient import TestClient
from app.main import app

# Importamos las herramientas necesarias: pytest para las pruebas, TestClient
# para simular peticiones a la API, y la aplicación FastAPI (app).

def test_rest_transcribe_wav():
    """
    Prueba el endpoint REST subiendo un archivo .wav.
    """
    # Usamos TestClient para simular una aplicación real, sin iniciar un servidor externo.
    with TestClient(app) as client:
        # Abrimos el archivo de audio de ejemplo ('1.wav') en modo binario ('rb').
        with open("samples/1.wav", "rb") as audio_file:
            # Enviamos una petición POST al endpoint '/transcribe'.
            # Usamos 'files' para simular la subida de un archivo.
            response = client.post(
                "/transcribe",
                files={"file": ("1.wav", audio_file, "audio/wav")}
            )
        
        # 1. Verificamos que la petición fue exitosa (código 200 OK).
        assert response.status_code == 200
        # Convertimos la respuesta JSON a un diccionario de Python.
        data = response.json()
        # 2. Verificamos que la respuesta JSON tiene la clave 'text' (la transcripción).
        assert "text" in data
        # 3. Verificamos que la transcripción contiene la palabra clave esperada ("café").
        assert "café" in data["text"]
        print(f"\n[REST Test] Transcripción exitosa: '{data['text']}'")

def test_websocket_transcribe_simple():
    """
    Prueba el endpoint WebSocket enviando el audio completo.
    """
    with TestClient(app) as client:
        # 1. Establecemos la conexión WebSocket con el endpoint '/ws/transcribe'.
        with client.websocket_connect("/ws/transcribe") as websocket:
            # Enviamos el mensaje inicial al servidor con la configuración de audio.
            websocket.send_json({"type": "start", "sample_rate": 16000})
            print("\n[WebSocket Test] Handshake enviado.")

            # Abrimos el archivo de audio PCM (formato raw que requiere Vosk).
            with open("samples/1.pcm", "rb") as pcm_file:
                # 2. Leemos y enviamos el audio en pequeños "trozos" (chunks) al servidor.
                while True:
                    chunk = pcm_file.read(4000) # Leemos 4000 bytes de audio.
                    if not chunk:
                        break # Salimos si llegamos al final del archivo.
                    websocket.send_bytes(chunk)
            
            # 3. Enviamos un mensaje de "End Of File" (EOF) para indicar que el audio terminó.
            websocket.send_json({"type": "eof"})
            print("[WebSocket Test] Audio y EOF enviados.")

            received_final = False
            # 4. Entramos en un bucle para recibir los mensajes del servidor.
            while True:
                try:
                    data = websocket.receive_json()
                    print(f"[WebSocket Test] Recibido: {data}")
                    # Verificamos que el mensaje recibido tiene las claves 'type' y 'text'.
                    assert "type" in data
                    assert "text" in data
                    # Si el mensaje es el 'final' y contiene la palabra clave, marcamos como exitoso.
                    if data["type"] == "final" and "café" in data["text"]:
                        received_final = True
                except Exception:
                    # Cuando el servidor termina el proceso y cierra la conexión, salimos del bucle.
                    break
            
            # 5. La prueba solo pasa si recibimos el mensaje final correcto.
            assert received_final, "No se recibió un mensaje final con la transcripción correcta."