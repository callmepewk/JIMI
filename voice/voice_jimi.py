import sounddevice as sd
import numpy as np
import torch
import queue
import time
import threading
import whisper

from silero_vad import load_silero_vad, get_speech_timestamps

# INTEGRAÇÕES
from audio_ai import speak
from jimi.brain import process_command  # <- você vai implementar depois

# ================= CONFIG =================

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

SILENCE_LIMIT = 1.0
MIN_AUDIO_LEN = 0.4

WAKE_WORDS = ["jimi", "jimmy", "gmi"]

# ================= ESTADO =================

audio_queue = queue.Queue()
RUNNING = True

is_processing = False
lock = threading.Lock()

# ================= INIT =================

print("🔊 Carregando Whisper...")
whisper_model = whisper.load_model("base")

print("🧠 Carregando VAD...")
vad_model = load_silero_vad()

# ================= UTIL =================

from wake_word import detect_wake_word, extract_command

def clean_command(text):
    for w in WAKE_WORDS:
        text = text.replace(w, "")
    return text.strip()

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

# ================= AUDIO CALLBACK =================

def audio_callback(indata, frames, time_info, status):
    if status:
        print("⚠️ Audio:", status)

    audio_queue.put(indata.copy())

# ================= PROCESSAMENTO =================

def handle_text(text):
    global is_processing

    with lock:
        if is_processing:
            print("⏳ Já processando, ignorando...")
            return
        is_processing = True

    try:
        print("🧠 Você disse:", text)

        # WAKE WORD
        if not is_wake_word(text):
            return

        command = clean_command(text)

        if not command:
            speak("Pode falar.")
            return

        # PROCESSAMENTO CENTRAL (brain.py)
        response = process_command(command)

        if response:
            speak(response)

    finally:
        is_processing = False

# ================= LISTENER =================

def listen():
    print("🎤 JIMI ouvindo...")

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
                            target=process_audio,
                            args=(audio,),
                            daemon=True
                        ).start()

                    speaking = False
                    buffer = []

# ================= PIPELINE =================

def process_audio(audio):
    text = transcribe(audio)

    if text:
        handle_text(text)

# ================= CONTROLE =================

def stop():
    global RUNNING
    RUNNING = False