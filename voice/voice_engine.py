import pyttsx3
import threading
import queue
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JIMI.VoiceEngine")

class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self._setup_voice()
        
        # Inicia o worker de fala em background
        threading.Thread(target=self._speech_worker, daemon=True).start()

    def _setup_voice(self):
        voices = self.engine.getProperty('voices')
        # Tenta configurar para português brasileiro
        for v in voices:
            if "brazil" in v.name.lower() or "portuguese" in v.name.lower():
                self.engine.setProperty('voice', v.id)
                break
        self.engine.setProperty('rate', 185)

    def _speech_worker(self):
        while True:
            text = self.speech_queue.get()
            if text is None: break
            try:
                self.is_speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"Erro no TTS: {e}")
            finally:
                self.is_speaking = False
                self.speech_queue.task_done()

    def speak(self, text, interrupt=False):
        if interrupt:
            self.stop()
        if text:
            self.speech_queue.put(text)

    def stop(self):
        self.engine.stop()

# Instância única para importação global
engine_instance = VoiceEngine()
speak = engine_instance.speak