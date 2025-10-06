import asyncio
import websockets
import json

async def run_error_test():
    """
    Este cliente se conecta al WebSocket y envía un handshake inválido
    a propósito para probar el manejo de errores del servidor.
    """
    uri = "ws://localhost:8000/ws/transcribe"

    try:
        async with websockets.connect(uri) as websocket:
            print("Conectado al servidor WebSocket.")

            # 1. Enviar un mensaje de handshake INCORRECTO.
            # El servidor espera {"type": "start"}, pero enviaremos otra cosa.
            await websocket.send(json.dumps({
                "type": "peticion_incorrecta",
                "sample_rate": 16000
            }))
            print("Handshake inválido enviado.")

            # 2. Esperar la respuesta del servidor
            response = await websocket.recv()
            data = json.loads(response)

            print("\n--- Respuesta del Servidor ---")
            print(data)
            print("----------------------------")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"\nLa conexión fue cerrada por el servidor, como se esperaba.")
        print(f"Código: {e.code}, Razón: {e.reason}")


if __name__ == "__main__":
    asyncio.run(run_error_test())