import asyncio
import websockets
import json

async def run_test():
    uri = "ws://localhost:8000/ws/transcribe"

    async with websockets.connect(uri) as websocket:
        print("Conectado al servidor WebSocket.")

        # 1. Enviar el mensaje de handshake inicial
        await websocket.send(json.dumps({
            "type": "start",
            "sample_rate": 16000,
            "channels": 1
        }))
        print("Handshake enviado.")

        # 2. Enviar el archivo de audio en chunks
        with open("samples/3.pcm", "rb") as pcm_file:
            while True:
                audio_chunk = pcm_file.read(4000) # Un chunk de 4000 bytes
                if not audio_chunk:
                    break
                await websocket.send(audio_chunk)
                await asyncio.sleep(0.1) 
        
        # 3. Enviar el mensaje de fin de audio
        await websocket.send(json.dumps({"type": "eof"}))
        print("Archivo de audio enviado completamente.")

        # 4. Recibir todas las respuestas del servidor hasta que se cierre la conexión
        print("\n--- Transcripciones recibidas ---")
        try:
            async for message in websocket:
                response = json.loads(message)
                # Solo imprimimos si el texto no está vacío para que se vea más limpio
                if response.get("text"):
                    print(f"Tipo: {response['type']}, Texto: {response['text']}")
        except websockets.exceptions.ConnectionClosed:
            print("\nConexión cerrada por el servidor.")
        print("---------------------------------")


if __name__ == "__main__":
    asyncio.run(run_test())
