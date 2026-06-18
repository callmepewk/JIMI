import pyttsx3
import threading
import queue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JIMI.VoiceEngine")

class VoiceEngine:
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        
        # Iniciamos a thread primeiro. A inicialização do pyttsx3 ocorrerá dentro dela.
        threading.Thread(target=self._speech_worker, daemon=True).start()

    def _setup_voice(self, engine):
        """Configura o idioma nativo para Português do Brasil."""
        try:
            voices = engine.getProperty('voices')
            for v in voices:
                if "brazil" in v.name.lower() or "portuguese" in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break
            engine.setProperty('rate', 180)  # Velocidade natural de fala
        except Exception as e:
            logger.error(f"Falha ao calibrar propriedades de voz: {e}")

    def _speech_worker(self):
        """Worker isolado em Thread dedicado exclusivamente para renderizar o áudio."""
        # Inicialização segura dentro do contexto da própria Thread
        engine = pyttsx3.init()
        self._setup_voice(engine)
        
        while True:
            text = self.speech_queue.get()
            if text is None: 
                break
            try:
                self.is_speaking = True
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"Erro de renderização no pipeline TTS: {e}")
            finally:
                self.is_speaking = False
                self.speech_queue.task_done()

    def speak(self, text: str, interrupt=False):
        """Adiciona o texto à fila de fala de forma assíncrona."""
        if not text:
            return
        if interrupt:
            self.stop()
            
        # Remove caracteres especiais ou blocos de código extensos antes de ditar
        clean_text = text.replace("`", "").replace("*", "").strip()
        self.speech_queue.put(clean_text)

    def stop(self):
        """Limpa a fila de transmissão atual."""
        try:
            while not self.speech_queue.empty():
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
        except Exception:
            pass

    def is_busy(self):
        """Retorna True se o motor estiver falando."""
        return self.is_speaking    

# Instância unificada para o ecossistema
engine_instance = VoiceEngine()
speak = engine_instance.speak
stop = engine_instance.stop
is_busy = engine_instance.is_busy