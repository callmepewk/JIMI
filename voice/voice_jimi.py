import logging
import queue
import numpy as np
import sounddevice as sd
import whisper
import torch
from silero_vad import load_silero_vad, get_speech_timestamps

# Alinhamento de imports com o ecossistema central do JIMI
from core.brain import jimi_brain as brain
from voice.voice_engine import speak

logger = logging.getLogger("JIMI.VoiceListener")


class VoiceListener:
    def __init__(self):
        self.sample_rate = 16000
        self.is_running = True
        
        # Parâmetros estáveis de calibração do Silero VAD para 16kHz
        self.chunk_size_samples = 512  # Bloco exato exigido pelo modelo matemático
        self.silence_threshold_chunks = 28  # ~900ms de silêncio contínuo para fechar a frase
        
        print("[*] Carregando Modelos Neurais de Voz Locais (Aguarde)...")
        
        # Alocação inteligente de hardware (GPU se disponível para latência ultrabaixa)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"[VOICE] Inicializando Whisper e VAD utilizando o dispositivo: {self.device}")
        
        self.whisper_model = whisper.load_model("base", device=self.device)
        self.vad_model = load_silero_vad()
        
        self.audio_queue = queue.Queue()
        
        # Configuração estável do stream físico (blocksize fixo garante consistência no VAD)
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=self.chunk_size_samples,
            callback=self._callback
        )

    def _callback(self, indata, frames, time, status):
        """Captura os frames do microfone e joga na fila de processamento sem travar o driver."""
        if status:
            logger.warning(f"[AUDIO HARDWARE] Alerta de integridade: {status}")
        self.audio_queue.put(indata.copy())

    def transcribe(self, audio_data: np.ndarray) -> str:
        """Processa a matriz bruta e extrai o texto traduzido via Whisper Local."""
        try:
            # Normaliza o sinal de áudio de 16-bit PCM para Float32 [-1.0, 1.0]
            audio_np = audio_data.flatten().astype(np.float32) / 32768.0
            
            # Executa inferência local focando em PT para pular etapas de detecção de idioma
            result = self.whisper_model.transcribe(
                audio_np, 
                language="pt", 
                fp16=torch.cuda.is_available()
            )
            return result["text"].strip()
        except Exception as e:
            logger.error(f"[TRANSCRIPTION ERROR] Falha na inferência do Whisper: {e}")
            return ""

    def start_listening(self):
        """Loop contínuo de monitoramento acústico de background."""
        print("[✓] Escuta local ativa (Whisper + Silero VAD) operacional.")
        self.stream.start()
        
        audio_buffer = []
        speech_detected = False
        silence_counter = 0

        while self.is_running:
            try:
                # Coleta os blocos da fila com timeout para liberar a CPU se estiver em silêncio absoluto
                chunk = self.audio_queue.get(timeout=0.8)
                audio_buffer.append(chunk)
                
                # Prepara o tensor matemático para validação no Silero VAD
                chunk_float = chunk.flatten().astype(np.float32) / 32768.0
                chunk_tensor = torch.from_numpy(chunk_float)
                
                speech_timestamps = get_speech_timestamps(
                    chunk_tensor, 
                    self.vad_model, 
                    sampling_rate=self.sample_rate
                )
                
                if len(speech_timestamps) > 0:
                    if not speech_detected:
                        logger.info("[VAD] Voz humana detectada. Registrando stream...")
                        speech_detected = True
                    silence_counter = 0
                else:
                    if speech_detected:
                        silence_counter += 1
                
                # Se atingiu o teto de silêncio (fim da sentença), consolida e processa
                if speech_detected and silence_counter >= self.silence_threshold_chunks:
                    logger.info("[VAD] Fim de transmissão identificado. Computando áudio...")
                    
                    # Para o stream temporariamente para não capturar o som da resposta do próprio JIMI
                    self.stream.stop()
                    
                    full_audio = np.concatenate(audio_buffer, axis=0)
                    text_extracted = self.transcribe(full_audio)
                    
                    if text_extracted and len(text_extracted) > 1:
                        # Comunica à interface gráfica o que você acabou de falar por voz
                        self._mirror_to_gui(f"Pedro: {text_extracted}")
                        print(f"\nSr. Pedro (Voz) > {text_extracted}")
                        
                        # Processamento cognitivo
                        response = brain.think(text_extracted)
                        print(f"JIMI > {response}\n")
                        
                        # Mostra a resposta na tela e fala pelos alto-falantes
                        self._mirror_to_gui(response)
                        speak(response)
                    
                    # Reseta os controladores e reinicia a captura limpa do microfone
                    audio_buffer = []
                    speech_detected = False
                    silence_counter = 0
                    self.stream.start()
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[VOICE LOOP ERROR] Falha na iteração do pipeline de áudio: {e}")

    def _mirror_to_gui(self, text: str):
        """Injeta o texto de forma segura no barramento de tela se a GUI estiver rodando."""
        try:
            from gui import ui_signals
            ui_signals.update_text_signal.emit(text)
        except (ImportError, AttributeError):
            # Se a interface não estiver aberta, o log segue apenas pelo terminal de desenvolvimento
            pass

    def stop(self):
        """Descarrega os drivers do sistema operacional de forma segura."""
        self.is_running = False
        try:
            self.stream.stop()
            self.stream.close()
            logger.info("[VOICE] Recursos de captura de áudio finalizados.")
        except Exception:
            pass


# Instanciação global segura para o bootmaster do JIMI
listener_instance = VoiceListener()

def listen(callback=None):
    """Gatilho de inicialização para ser invocado via Thread secundária."""
    listener_instance.start_listening()


if __name__ == "__main__":
    # Permite testar o arquivo de áudio de forma isolada direto pelo terminal
    logging.basicConfig(level=logging.INFO)
    try:
        listener_instance.start_listening()
    except KeyboardInterrupt:
        listener_instance.stop()