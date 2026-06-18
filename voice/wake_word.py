import os
import logging
import glob
import pvporcupine
from pvrecorder import PvRecorder

logger = logging.getLogger("JIMI.WakeWord")

class WakeWordEngine:
    def __init__(self):
        """
        Engine de ativação ultra-leve via Picovoice Porcupine.
        Autodetecta chaves de ambiente e arquivos de modelo (.ppn).
        """
        # 1. Resolução da Access Key (Var de ambiente -> Fallback Hardcoded)
        self.access_key = os.getenv("PICOVOICE_ACCESS_KEY", "SUA_ACCESS_KEY_AQUI")
        
        if self.access_key == "SUA_ACCESS_KEY_AQUI" or not self.access_key:
            raise ValueError(
                "\n[ERRO CRÍTICO] Chave do Picovoice não configurada!\n"
                "Defina a variável de ambiente 'PICOVOICE_ACCESS_KEY' ou edite o arquivo config."
            )

        # 2. Varredura Automática de arquivos .ppn na pasta local 'voice/'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ppn_files = glob.glob(os.path.join(current_dir, "*.ppn"))

        if ppn_files:
            # Seleciona o primeiro arquivo customizado encontrado (ex: jimi.ppn)
            self.keyword_path = ppn_files[0]
            logger.info(f"[PORCUPINE] Modelo customizado autodetectado: {os.path.basename(self.keyword_path)}")
            self.porcupine = pvporcupine.create(
                access_key=self.access_key, 
                keyword_paths=[self.keyword_path]
            )
        else:
            # Caso não tenha gerado o .ppn ainda, usa o fallback nativo estável
            logger.warning("[PORCUPINE] Nenhum arquivo .ppn achado em /voice. Usando keyword nativa 'jarvis'.")
            self.porcupine = pvporcupine.create(
                access_key=self.access_key, 
                keywords=['jarvis']
            )
            
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.is_running = False

    def listen_for_wake(self) -> bool:
        """Bloqueia a execução e escuta o ambiente até detectar a wake word."""
        try:
            self.recorder.start()
            self.is_running = True
            
            while self.is_running:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)

                if result >= 0:
                    logger.info("[PORCUPINE] Gatilho de voz disparado!")
                    self.stop_recorder()
                    return True
        except Exception as e:
            logger.error(f"[PORCUPINE ERROR] Falha no loop de escuta passiva: {e}")
            self.stop_recorder()
        return False

    def stop_recorder(self):
        """Para temporariamente o gravador para liberar o microfone para o Whisper."""
        if self.is_running:
            self.is_running = False
            try:
                self.recorder.stop()
            except Exception:
                pass

    def release(self):
        """Destrói as instâncias de hardware do Picovoice ao encerrar o sistema."""
        try:
            self.stop_recorder()
            self.recorder.delete()
            self.porcupine.delete()
            logger.info("[PORCUPINE] Recursos de hardware liberados.")
        except Exception:
            pass

# Inicialização global segura da instância
try:
    wake_engine = WakeWordEngine()
except Exception as err:
    logger.error(f"Falha ao subir subsistema Porcupine: {err}")
    wake_engine = None