import asyncio
import websockets
import json

async def run_abrupt_close_test():
    """
    Este cliente envía audio y luego cierra la conexión abruptamente
    sin enviar un mensaje {"type": "eof"}, para probar la robustez del servidor.
    """
    uri = "ws://localhost:8000/ws/transcribe"

    # El 'async with' asegura que la conexión se cierre al final del bloque
    async with websockets.connect(uri) as websocket:
        print("Conectado al servidor WebSocket.")

        # 1. Enviar handshake
        await websocket.send(json.dumps({
            "type": "start",
            "sample_rate": 16000
        }))
        print("Handshake enviado.")

        # 2. Enviar el archivo de audio
        with open("samples/1.pcm", "rb") as pcm_file:
            audio_data = pcm_file.read()
            await websocket.send(audio_data)
            print("Audio enviado de una sola vez.")

    # 3. Al salir del bloque 'async with', el socket se cierra sin enviar "eof".
    print("\nEl cliente ha cerrado la conexión abruptamente.")


if __name__ == "__main__":
    asyncio.run(run_abrupt_close_test())
