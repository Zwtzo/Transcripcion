import asyncio
import websockets
import json

# Cliente de prueba para el escenario: "enviar todo el audio en un solo chunk y recibir la respuesta final".

async def run_single_chunk_test():
    """
    Este cliente envía un archivo de audio completo en un solo mensaje binario,
    envía una señal de fin de archivo (eof) y luego espera para recibir
    la transcripción final del servidor.
    """
    uri = "ws://localhost:8000/ws/transcribe"

    async with websockets.connect(uri) as websocket:
        print("Conectado al servidor WebSocket.")

        # 1. Enviar handshake
        await websocket.send(json.dumps({
            "type": "start",
            "sample_rate": 16000,
            "channels": 1
        }))
        print("Handshake enviado.")

        # 2. Enviar el archivo de audio completo en un solo chunk
        with open("samples/1.pcm", "rb") as pcm_file:
            audio_data = pcm_file.read()
            await websocket.send(audio_data)
            print("Audio enviado de una sola vez.")

        # 3. Enviar el mensaje de fin de audio para un cierre limpio
        await websocket.send(json.dumps({"type": "eof"}))
        print("Mensaje 'eof' enviado.")

        # 4. Escuchar las respuestas del servidor
        print("\n--- Esperando transcripción final ---")
        final_transcription_received = False
        try:
            async for message in websocket:
                response = json.loads(message)
                if response.get("text"):
                    print(f"Tipo: {response['type']}, Texto: {response['text']}")
                    if response['type'] == 'final':
                        final_transcription_received = True
        except websockets.exceptions.ConnectionClosed:
            print("\nConexión cerrada por el servidor.")

        # 5. Verificación final
        if final_transcription_received:
            print("\nPrueba exitosa: Se recibió la transcripción final.")
        else:
            print("\nPrueba fallida: No se recibió una transcripción de tipo 'final'.")
        print("------------------------------------")


if __name__ == "__main__":
    asyncio.run(run_single_chunk_test())
