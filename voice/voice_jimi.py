import sounddevice as sd
import numpy as np
import threading
import whisper
from silero_vad import load_silero_vad, get_speech_timestamps
from wake_word import detect_wake_word, extract_command
from audio_ai import speak
from jimi.automation import jimi_core  # Importando nossa classe robusta

class VoiceListener:
    def __init__(self):
        self.sample_rate = 16000
        self.whisper_model = whisper.load_model("base")
        self.vad_model = load_silero_vad()
        self.is_running = True
        self.audio_queue = sd.InputStream(samplerate=self.sample_rate, channels=1, callback=self._callback)

    def _callback(self, indata, frames, time, status):
        # Aqui, em um sistema real, colocaríamos em uma fila circular
        pass

    def transcribe(self, audio_data):
        """Converte áudio para texto com Whisper"""
        audio_np = audio_data.flatten().astype(np.float32) / 32768.0
        result = self.whisper_model.transcribe(audio_np, language="pt", fp16=False)
        return result["text"].strip().lower()

    def run_pipeline(self, audio_chunk):
        """Pipeline: Ouve -> Transcreve -> Verifica Wake Word -> Executa"""
        text = self.transcribe(audio_chunk)
        
        if detect_wake_word(text):
            command = extract_command(text)
            if command:
                # Chama o cérebro (JimiAutomation)
                response = jimi_core.process_command(command)
                speak(response)
            else:
                speak("Estou aqui, Sr. Pedro.")

    def start_listening(self):
        print("JIMI: Sistema de escuta online.")
        # O loop principal de captura será aqui