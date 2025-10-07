import asyncio
import websockets
import json

# Importamos las librerías necesarias:
# asyncio: para manejar operaciones asíncronas.
# websockets: para crear el cliente WebSocket.
# json: para codificar y decodificar los mensajes de protocolo.

async def run_test():
    # Define la dirección del servidor WebSocket.
    uri = "ws://localhost:8000/ws/transcribe"

    # Inicia la conexión WebSocket. El 'async with' garantiza que la conexión
    # se establezca correctamente y se cierre al salir del bloque.
    async with websockets.connect(uri) as websocket:
        print("Conectado al servidor WebSocket.")

        # 1. Enviar el mensaje de handshake inicial
        # Enviamos un mensaje JSON inicial con los parámetros del audio (tasa de muestreo, etc.).
        await websocket.send(json.dumps({
            "type": "start",
            "sample_rate": 16000,
            "channels": 1
        }))
        print("Handshake enviado.")

        # 2. Enviar el archivo de audio en chunks (simulando un stream en vivo)
        with open("samples/3.pcm", "rb") as pcm_file:
            # Leemos el archivo en un bucle.
            while True:
                # Leemos un "trozo" (chunk) de 4000 bytes.
                audio_chunk = pcm_file.read(4000) 
                if not audio_chunk:
                    break # Salimos del bucle si ya no hay más datos.
                await websocket.send(audio_chunk) # Enviamos los bytes de audio.
                # Esperamos brevemente para simular un stream de audio en tiempo real.
                await asyncio.sleep(0.1) 
        
        # 3. Enviar el mensaje de fin de audio
        # Indica al servidor que se ha terminado de enviar el audio (End Of File).
        await websocket.send(json.dumps({"type": "eof"}))
        print("Archivo de audio enviado completamente.")

        # 4. Recibir todas las respuestas del servidor hasta que se cierre la conexión
        print("\n--- Transcripciones recibidas ---")
        try:
            # Bucle asíncrono para recibir mensajes del servidor (resultados parciales y finales).
            async for message in websocket:
                response = json.loads(message)
                # Solo imprimimos si el resultado de la transcripción tiene texto.
                if response.get("text"):
                    print(f"Tipo: {response['type']}, Texto: {response['text']}")
        except websockets.exceptions.ConnectionClosed:
            # Se ejecuta cuando el servidor finaliza la transcripción y cierra la conexión.
            print("\nConexión cerrada por el servidor.")
        print("---------------------------------")


if __name__ == "__main__":
    # Inicia el bucle de eventos de asyncio para ejecutar la función principal.
    asyncio.run(run_test())