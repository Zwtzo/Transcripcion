import asyncio
import websockets
import json

# Importamos las librerías necesarias para crear un cliente asíncrono de WebSocket.

async def run_abrupt_close_test():
    """
    Este cliente envía audio y luego cierra la conexión abruptamente
    sin enviar un mensaje {"type": "eof"}, para probar la robustez del servidor.
    """
    uri = "ws://localhost:8000/ws/transcribe"

    # El 'async with' gestiona la conexión. Cuando el bloque termina,
    # llama automáticamente al cierre del socket, simulando un cierre abrupto
    # si no enviamos un mensaje de cierre explícito (como 'eof').
    async with websockets.connect(uri) as websocket:
        print("Conectado al servidor WebSocket.")

        # 1. Enviar handshake
        # Enviamos el mensaje JSON inicial para configurar la tasa de muestreo (sample_rate).
        await websocket.send(json.dumps({
            "type": "start",
            "sample_rate": 16000
        }))
        print("Handshake enviado.")

        # 2. Enviar el archivo de audio
        with open("samples/1.pcm", "rb") as pcm_file:
            # Leemos todo el archivo de audio de ejemplo de una vez.
            audio_data = pcm_file.read()
            # Enviamos todos los bytes de audio al servidor.
            await websocket.send(audio_data)
            print("Audio enviado de una sola vez.")

    # 3. Cierre abrupto
    # La ejecución sale del bloque 'async with'. Esto provoca que la librería
    # 'websockets' cierre el socket sin enviar un mensaje de protocolo formal.
    # El servidor debe capturar esta desconexión inesperada (WebSocketDisconnect).
    print("\nEl cliente ha cerrado la conexión abruptamente.")


if __name__ == "__main__":
    # La función 'asyncio.run' inicia el bucle de eventos para ejecutar la función asíncrona.
    asyncio.run(run_abrupt_close_test())