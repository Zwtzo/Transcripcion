import asyncio
import websockets
import json

# Importamos las herramientas asíncronas, de WebSocket y de JSON.

async def run_error_test():
    """
    Este cliente se conecta al WebSocket y envía un handshake inválido
    a propósito para probar el manejo de errores del servidor.
    """
    # Definimos la dirección del endpoint de WebSocket.
    uri = "ws://localhost:8000/ws/transcribe"

    try:
        # Iniciamos la conexión. Si todo va bien, nos conectamos.
        async with websockets.connect(uri) as websocket:
            print("Conectado al servidor WebSocket.")

            # 1. Enviar un mensaje de handshake INCORRECTO.
            # Según el protocolo de nuestra API, el primer mensaje debe ser {"type": "start"}.
            # Aquí, enviamos intencionalmente "type": "peticion_incorrecta" para forzar un error.
            await websocket.send(json.dumps({
                "type": "peticion_incorrecta",
                "sample_rate": 16000,
                "channels": 1
            }))
            print("Handshake inválido enviado.")

            # 2. Esperar la respuesta del servidor
            # El servidor debería responder con un mensaje JSON de error (type: "error").
            response = await websocket.recv()
            data = json.loads(response)

            # Imprimimos lo que recibimos, esperando ver el mensaje de error.
            print("\n--- Respuesta del Servidor ---")
            print(data)
            print("----------------------------")

    except websockets.exceptions.ConnectionClosed as e:
        # Después de que el servidor envía el mensaje de error, cerrará la conexión (cierre esperado).
        # Capturamos esa excepción para informar que el test fue exitoso.
        print(f"\nLa conexión fue cerrada por el servidor, como se esperaba.")
        # Podemos ver el código de cierre del protocolo (esperaríamos 1008, 'Violación de Política').
        print(f"Código: {e.code}, Razón: {e.reason}")


if __name__ == "__main__":
    # Ejecutamos la función principal asíncrona.
    asyncio.run(run_error_test())