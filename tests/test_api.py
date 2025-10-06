import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_rest_transcribe_wav():
    """
    Prueba el endpoint REST subiendo un archivo .wav.
    """
    with TestClient(app) as client:
        with open("samples/1.wav", "rb") as audio_file:
            response = client.post(
                "/transcribe",
                files={"file": ("1.wav", audio_file, "audio/wav")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        # Verificamos que la transcripción contiene la palabra esperada
        assert "café" in data["text"]
        print(f"\n[REST Test] Transcripción exitosa: '{data['text']}'")

def test_websocket_transcribe_simple():
    """
    Prueba el endpoint WebSocket enviando el audio completo.
    """
    with TestClient(app) as client:
        with client.websocket_connect("/ws/transcribe") as websocket:
            websocket.send_json({"type": "start", "sample_rate": 16000})
            print("\n[WebSocket Test] Handshake enviado.")

            # --- INICIO DE LA CORRECCIÓN ---
            # Ahora enviamos el archivo completo en un bucle
            with open("samples/1.pcm", "rb") as pcm_file:
                while True:
                    chunk = pcm_file.read(4000) # Leemos un trozo
                    if not chunk:
                        break # Si no hay más datos, salimos del bucle
                    websocket.send_bytes(chunk)
            # --- FIN DE LA CORRECCIÓN ---
            
            websocket.send_json({"type": "eof"})
            print("[WebSocket Test] Audio y EOF enviados.")

            received_final = False
            while True:
                try:
                    data = websocket.receive_json()
                    print(f"[WebSocket Test] Recibido: {data}")
                    assert "type" in data
                    assert "text" in data
                    if data["type"] == "final" and "café" in data["text"]:
                        received_final = True
                except Exception:
                    # La conexión se cierra después de que el servidor envía el último mensaje.
                    # Esto es esperado, por lo que rompemos el bucle.
                    break
            
            assert received_final, "No se recibió un mensaje final con la transcripción correcta."

