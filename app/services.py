from vosk import Model, KaldiRecognizer # <-- AÑADE ESTO

# Importamos las clases necesarias de la librería Vosk.
# 'Model' se usa para cargar los archivos del modelo de voz.
# 'KaldiRecognizer' se usa para procesar el audio y obtener la transcripción.

# Declaramos una variable global que contendrá el modelo de Vosk cargado.
# Se inicializa a None y se llena solo una vez al inicio de la aplicación.
VOSK_MODEL = None

def load_vosk_model():
    """Carga el modelo de Vosk desde la carpeta 'model'."""
    # Usamos 'global' para indicar que vamos a modificar la variable VOSK_MODEL
    # que está definida fuera de esta función.
    global VOSK_MODEL
    
    # Creamos una instancia del objeto Model, indicando la ruta donde se encuentra el modelo.
    # Este proceso solo debe ejecutarse una vez al iniciar la API (como se ve en app.main).
    VOSK_MODEL = Model("model")
    
    print("Modelo de Vosk cargado exitosamente.")