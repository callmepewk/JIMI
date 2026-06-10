import pyttsx3
import threading
import queue
import time

# ==============================
# CONFIG
# ==============================

VOICE_RATE = 185
VOICE_VOLUME = 1.0
VOICE_ID = None  # pode definir depois

DEBUG = True

# ==============================
# ENGINE
# ==============================

engine = pyttsx3.init()

def log(*args):
    if DEBUG:
        print("[AUDIO]", *args)

def setup_voice():
    global engine

    voices = engine.getProperty('voices')

    # 🔥 tenta escolher voz mais natural
    if VOICE_ID:
        engine.setProperty('voice', VOICE_ID)
    else:
        for v in voices:
            if "brazil" in v.name.lower() or "portuguese" in v.name.lower():
                engine.setProperty('voice', v.id)
                break

    engine.setProperty('rate', VOICE_RATE)
    engine.setProperty('volume', VOICE_VOLUME)

setup_voice()

# ==============================
# FILA DE ÁUDIO (NÃO BLOQUEANTE)
# ==============================

speech_queue = queue.Queue()
is_speaking = False
stop_signal = False

def _speech_worker():
    global is_speaking, stop_signal

    while True:
        text = speech_queue.get()

        if text is None:
            continue

        try:
            is_speaking = True
            log("Falando:", text)

            engine.say(text)
            engine.runAndWait()

        except Exception as e:
            log("Erro TTS:", e)

        finally:
            is_speaking = False
            speech_queue.task_done()

# thread separada (ESSENCIAL)
threading.Thread(target=_speech_worker, daemon=True).start()

# ==============================
# API PRINCIPAL
# ==============================

def speak(text, interrupt=False):
    global stop_signal

    if not text:
        return

    # 🔥 se quiser interromper fala atual
    if interrupt:
        stop()

    speech_queue.put(text)

# ==============================
# CONTROLE
# ==============================

def stop():
    global stop_signal

    try:
        engine.stop()
        log("Fala interrompida")
    except:
        pass


def is_busy():
    return is_speaking


def wait_until_done():
    speech_queue.join()

# ==============================
# CONFIG DINÂMICA
# ==============================

def set_rate(rate):
    engine.setProperty('rate', rate)


def set_volume(volume):
    engine.setProperty('volume', volume)


def list_voices():
    voices = engine.getProperty('voices')
    return [(v.id, v.name) for v in voices]