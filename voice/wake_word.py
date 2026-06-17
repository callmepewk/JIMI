import os
import struct
import pvporcupine
from pvrecorder import PvRecorder

class WakeWordEngine:
    def __init__(self, access_key, model_path=None, keyword_paths=None):
        """
        access_key: Sua chave obtida no console.picovoice.ai
        """
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=keyword_paths
        )
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.is_running = False

    def start(self, callback_on_wake):
        self.recorder.start()
        self.is_running = True
        print("JIMI: Wake word engine ativa e escutando...")

        try:
            while self.is_running:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)

                if result >= 0:
                    callback_on_wake()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.is_running = False
        self.recorder.stop()
        self.recorder.delete()
        self.porcupine.delete()

# --- Integração com o fluxo do sistema ---
def on_wake_detected():
    print("JIMI: Sim, Sr. Pedro? O que o senhor deseja?")
    # Aqui chamaremos a função de reconhecimento de voz (Speech-to-Text)
    # que passará o comando para o automation.py

if __name__ == "__main__":
    # A chave de acesso é gratuita no site da Picovoice
    ACCESS_KEY = "SUA_ACCESS_KEY_AQUI"
    engine = WakeWordEngine(ACCESS_KEY)
    engine.start(on_wake_detected)