import sounddevice as sd
import numpy as np
import torch
import queue
import time
import threading

# IA
from core.brain import think

def main():
    print("JIMI iniciado. Digite algo:")

    while True:
        user_input = input("Você: ")

        if user_input.lower() in ["sair", "exit", "quit"]:
            break

        resposta = think(user_input)
        print("Jimi:", resposta)

if __name__ == "__main__":
    main()

from silero_vad import load_silero_vad, get_speech_timestamps
import whisper
import pyttsx3

# ================= CONFIG =================

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

SILENCE_LIMIT = 1.0
MIN_AUDIO_LEN = 0.4

WAKE_WORD = "jimi"  # (temporário - depois Porcupine)

# ================= ESTADO =================

audio_queue = queue.Queue()
tts_queue = queue.Queue()

ACTIVE_MODE = False
RUNNING = True

# ================= INIT =================

print("🔊 Carregando Whisper...")
whisper_model = whisper.load_model("base")

print("🧠 Carregando VAD...")
vad_model = load_silero_vad()

print("🔈 Inicializando voz...")
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
    audio_np = audio.flatten().astype(np.float32) / 32768.0

    result = whisper_model.transcribe(
        audio_np,
        language="pt",
        fp16=False
    )

    return result["text"].strip().lower()

# ================= PROCESSAMENTO =================

def process_audio(audio):
    global ACTIVE_MODE

    try:
        text = transcribe(audio)

        if not text:
            return

        print("🧠 Você disse:", text)

        # ================= WAKE WORD =================

        if WAKE_WORD in text:
            ACTIVE_MODE = True
            speak("Sim?")
            return

        if not ACTIVE_MODE:
            return

        # ================= DESATIVAR =================

        if any(cmd in text for cmd in ["parar", "fica quieto", "desativar"]):
            ACTIVE_MODE = False
            speak("Modo silencioso ativado")
            return

        # ================= IA =================

        response = think(text)

        if response:
            speak(response)

    except Exception as e:
        print("❌ Erro processamento:", e)

# ================= AUDIO =================

def audio_callback(indata, frames, time_info, status):
    if status:
        print("⚠️ Audio:", status)

    audio_queue.put(indata.copy())

# ================= LISTENER =================

def listener_loop():
    print("🎤 Jimi ativo (modo contínuo)")

    buffer = []
    speaking = False
    last_voice = time.time()
    start_time = None

    while RUNNING:
        data = audio_queue.get()

        if detect_speech(data):

            if not speaking:
                speaking = True
                buffer = []
                start_time = time.time()
                print("🟢 Fala iniciada")

            buffer.append(data)
            last_voice = time.time()

        else:
            if speaking and (time.time() - last_voice > SILENCE_LIMIT):

                duration = time.time() - start_time

                if duration > MIN_AUDIO_LEN:
                    print("🔴 Processando...")

                    audio = np.concatenate(buffer, axis=0)

                    threading.Thread(
                        target=process_audio,
                        args=(audio,),
                        daemon=True
                    ).start()

                speaking = False
                buffer = []

# ================= START =================

def start():
    stream = sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE
    )

    with stream:
        listener_loop()

# ================= RUN =================

if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando Jimi...")