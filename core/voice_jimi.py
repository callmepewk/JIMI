import sounddevice as sd
import numpy as np
import torch
import queue
import time
import threading
import whisper
import pyttsx3
from silero_vad import load_silero_vad, get_speech_timestamps

# ================= CONFIG =================

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

SILENCE_LIMIT = 1.0
MIN_AUDIO_LEN = 0.4

# ================= ESTADO =================

audio_queue = queue.Queue()
tts_queue = queue.Queue()

RUNNING = True

# ================= INIT =================

print("🔊 Carregando Whisper...")
whisper_model = whisper.load_model("base")

print("🧠 Carregando VAD...")
vad_model = load_silero_vad()

print("🔈 Inicializando TTS...")
engine = pyttsx3.init()
engine.setProperty("rate", 185)

# ================= TTS =================

def tts_worker():
    while RUNNING:
        text = tts_queue.get()
        if text:
            print("🤖:", text)
            engine.say(text)
            engine.runAndWait()

def speak(text):
    tts_queue.put(text)

threading.Thread(target=tts_worker, daemon=True).start()

# ================= VAD =================

def detect_speech(audio):
    audio = audio.flatten()
    audio_tensor = torch.from_numpy(audio).float()

    speech = get_speech_timestamps(
        audio_tensor,
        vad_model,
        sampling_rate=SAMPLE_RATE
    )

    return len(speech) > 0

# ================= TRANSCRIÇÃO =================

def transcribe(audio):
    try:
        audio_np = audio.flatten().astype(np.float32) / 32768.0

        result = whisper_model.transcribe(
            audio_np,
            language="pt",
            fp16=False
        )

        return result["text"].strip().lower()

    except Exception as e:
        print("❌ Erro transcrição:", e)
        return ""

# ================= PIPELINE DE CAPTURA =================

def audio_callback(indata, frames, time_info, status):
    if status:
        print("⚠️ Audio:", status)

    audio_queue.put(indata.copy())

# ================= LISTENER =================

def listen(on_speech_detected):
    """
    Loop principal de escuta.
    Quando detectar fala válida, chama:
    on_speech_detected(texto)
    """

    print("🎤 Módulo de voz ativo")

    buffer = []
    speaking = False
    last_voice = time.time()
    start_time = None

    stream = sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE
    )

    with stream:
        while RUNNING:
            data = audio_queue.get()

            if detect_speech(data):

                if not speaking:
                    speaking = True
                    buffer = []
                    start_time = time.time()
                    print("🟢 Fala detectada")

                buffer.append(data)
                last_voice = time.time()

            else:
                if speaking and (time.time() - last_voice > SILENCE_LIMIT):

                    duration = time.time() - start_time

                    if duration > MIN_AUDIO_LEN:
                        print("🔴 Processando fala...")

                        audio = np.concatenate(buffer, axis=0)

                        threading.Thread(
                            target=process_and_callback,
                            args=(audio, on_speech_detected),
                            daemon=True
                        ).start()

                    speaking = False
                    buffer = []

# ================= PROCESSAMENTO =================

def process_and_callback(audio, callback):
    text = transcribe(audio)

    if text:
        print("🧠 Você disse:", text)
        callback(text)

# ================= CONTROLE =================

def stop():
    global RUNNING
    RUNNING = False