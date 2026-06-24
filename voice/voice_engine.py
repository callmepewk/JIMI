import pyttsx3
import threading
import queue
import logging
import platform
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JIMI.VoiceEngine")

class VoiceEngine:
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.sistema_operacional = platform.system().lower()
        
        # Volumes padrao para o efeito Alexa (Ducking)
        self.VOLUME_MUSICA_NORMAL = 12  # Escala Termux vai de 0 a 15
        self.VOLUME_MUSICA_ABAFADO = 3
        
        # Iniciamos a thread primeiro. A inicializacao do pyttsx3 ocorrera dentro dela.
        threading.Thread(target=self._speech_worker, daemon=True).start()

    def _setup_voice(self, engine):
        """Configura o idioma nativo para Portugues do Brasil."""
        try:
            voices = engine.getProperty('voices')
            for v in voices:
                if "brazil" in v.name.lower() or "portuguese" in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break
            engine.setProperty('rate', 180)  # Velocidade natural de fala
        except Exception as e:
            logger.error(f"Falha ao calibrar propriedades de voz: {e}")

    def _controlar_volume_sistema(self, abaixar: bool):
        """Abaixa ou aumenta o som de fundo baseado no dispositivo atual (Efeito Alexa)."""
        try:
            if "linux" in self.sistema_operacional:
                # Se estiver rodando dentro do Termux no Moto G7
                volume = self.VOLUME_MUSICA_ABAFADO if abaixar else self.VOLUME_MUSICA_NORMAL
                # Altera o canal de midia/musica do Android instantaneamente
                os.system(f"termux-volume music {volume}")
            elif "windows" in self.sistema_operacional:
                # Logs de depuracao se estiver testando a engine no PC master
                if abaixar:
                    logger.info("[Ducking] Abafando midias de fundo no Windows...")
                else:
                    logger.info("[Ducking] Restaurando volumes no Windows...")
        except Exception as e:
            logger.error(f"Falha ao gerenciar Ducking de audio: {e}")

    def _speech_worker(self):
        """Worker isolado em Thread dedicado exclusivamente para renderizar o audio."""
        engine = pyttsx3.init()
        self._setup_voice(engine)
        
        while True:
            text = self.speech_queue.get()
            if text is None: 
                break
            try:
                self.is_speaking = True
                
                # 1. Efeito Alexa: Abafa o som do ambiente antes de falar
                self._controlar_volume_sistema(abaixar=True)
                
                # 2. Emite a fala do JIMI
                engine.say(text)
                engine.runAndWait()
                
            except Exception as e:
                logger.error(f"Erro de renderizacao no pipeline TTS: {e}")
            finally:
                self.is_speaking = False
                
                # 3. Restaura o volume original da musica imediatamente apos terminar de falar
                self._controlar_volume_sistema(abaixar=False)
                self.speech_queue.task_done()

    def speak(self, text: str, interrupt=False):
        """Adiciona o texto a fila de fala de forma assincrona."""
        if not text:
            return
        if interrupt:
            self.stop()
            
        clean_text = text.replace("`", "").replace("*", "").strip()
        self.speech_queue.put(clean_text)

    def stop(self):
        """Limpa a fila de transmissao atual e garante restauracao do som."""
        try:
            while not self.speech_queue.empty():
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            self._controlar_volume_sistema(abaixar=False)
        except Exception:
            pass

    def is_busy(self):
        """Retorna True se o motor estiver falando."""
        return self.is_speaking    

# Instancia unificada para o ecossistema
engine_instance = VoiceEngine()
speak = engine_instance.speak
stop = engine_instance.stop
is_busy = engine_instance.is_busy