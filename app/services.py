# app/services.py
from vosk import Model, KaldiRecognizer # <-- AÑADE ESTO

VOSK_MODEL = None

def load_vosk_model():
    """Carga el modelo de Vosk desde la carpeta 'model'."""
    global VOSK_MODEL
    VOSK_MODEL = Model("model")
    print("Modelo de Vosk cargado exitosamente.")