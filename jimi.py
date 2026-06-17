import threading
import signal
import sys
from brain import brain  # Nosso novo cérebro cognitivo
from voice.voice_engine import speak
from voice.audio_ai import listen

class JimiSystem:
    def __init__(self):
        self.running = True
        self.active_mode = False
        
    def start(self):
        print("\n=== SISTEMA JIMI ATIVADO ===")
        # Inicia a thread de escuta
        threading.Thread(target=self._voice_listener_thread, daemon=True).start()
        # Inicia o modo CLI
        self._cli_loop()

    def _voice_listener_thread(self):
        # A lógica de escuta chama o cérebro diretamente
        listen(callback=self._handle_voice_input)

    def _handle_voice_input(self, text):
        """Ponte entre a escuta de voz e o processamento cerebral."""
        if not text: return
        
        # Wake word check...
        # Se ativo, chama brain.think(text)
        response = brain.think(text)
        speak(response)

    def _cli_loop(self):
        while self.running:
            user_input = input("Você: ")
            if user_input.lower() in ["sair", "exit"]:
                self.shutdown()
                break
            
            response = brain.think(user_input)
            print(f"Jimi: {response}")
            speak(response)

    def shutdown(self, signum=None, frame=None):
        self.running = False
        print("\n🛑 Desativando protocolos de segurança...")
        sys.exit(0)

if __name__ == "__main__":
    jimi = JimiSystem()
    signal.signal(signal.SIGINT, jimi.shutdown)
    jimi.start()