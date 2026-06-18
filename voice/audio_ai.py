import logging
import os
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JIMI.AudioAI")

# --- CORREÇÃO DE ROTA DE IMPORTAÇÃO ---
try:
    from voice.voice_engine import speak as engine_speak, stop as engine_stop, is_busy as engine_is_busy
except ModuleNotFoundError:
    from voice_engine import speak as engine_speak, stop as engine_stop, is_busy as engine_is_busy

# ==========================================
# SEÇÃO 1: TEXT-TO-SPEECH (SAÍDA DE ÁUDIO)
# ==========================================

def speak(text, interrupt=False):
    """Função principal para o JIMI falar."""
    engine_speak(text, interrupt=interrupt)

def stop():
    """Interrompe a fala atual do JIMI imediatamente."""
    engine_stop()

def is_speaking():
    """Retorna True se o JIMI estiver falando no momento."""
    return engine_is_busy()


# ==========================================
# SEÇÃO 2: SPEECH-TO-TEXT (ENTRADA DE ÁUDIO VIA SOUNDDEVICE)
# ==========================================

def listen_command(timeout=5, phrase_limit=5) -> str:
    """
    Escuta o microfone gravando um bloco rápido de áudio usando sounddevice.
    Livre de dependências quebradas de compilação em C.
    """
    recognizer = sr.Recognizer()
    sample_rate = 16000
    temp_filename = "temp_command.wav"
    
    try:
        logger.info(f"JIMI está ouvindo (capturando bloco de {phrase_limit}s)...")
        # Captura o áudio do microfone padrão do Windows
        audio_data = sd.rec(int(phrase_limit * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()  # Aguarda a gravação do bloco finalizar
        
        # Salva temporariamente o arquivo de áudio
        sf.write(temp_filename, audio_data, sample_rate)
        
        # Alimenta o reconhecedor do Google com o arquivo local
        with sr.AudioFile(temp_filename) as source:
            audio_file_data = recognizer.record(source)
            
        logger.info("Processando áudio capturado...")
        text = recognizer.recognize_google(audio_file_data, language="pt-BR")
        logger.info(f"Transcrição ativa: {text}")
        return text.strip()
        
    except sr.UnknownValueError:
        logger.info("Nenhum comando claro identificado no bloco.")
        return ""
    except Exception as e:
        logger.error(f"Falha na captura via sounddevice: {e}")
        return ""
    finally:
        # Garante a limpeza do arquivo temporário do seu disco
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


def listen_dictation_until_keyword(keyword="ponto") -> str:
    """
    Grava blocos sequenciais de áudio e transcreve em tempo real.
    Para a execução imediatamente quando você disser a palavra 'ponto'.
    """
    recognizer = sr.Recognizer()
    sample_rate = 16000
    temp_filename = "temp_dictate.wav"
    full_text_blocks = []
    block_duration = 5  # Segundos por bloco de fala
    
    logger.info(f"Modo Ditado Ativo. Fale em blocos e encerre dizendo apenas '{keyword}'.")
    
    while True:
        try:
            logger.info("[Ditado] Escutando próximo bloco...")
            audio_data = sd.rec(int(block_duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            
            sf.write(temp_filename, audio_data, sample_rate)
            
            with sr.AudioFile(temp_filename) as source:
                audio_file_data = recognizer.record(source)
                
            text = recognizer.recognize_google(audio_file_data, language="pt-BR").strip()
            logger.info(f"[Ditado] Capturado: {text}")
            
            # Verifica o gatilho de parada ("ponto")
            if text.lower() == keyword.lower() or text.lower().endswith(f" {keyword.lower()}"):
                if text.lower().endswith(f" {keyword.lower()}"):
                    clean_block = text[:-len(keyword)].strip()
                    if clean_block:
                        full_text_blocks.append(clean_block)
                break
                
            if text:
                full_text_blocks.append(text)
                
        except sr.UnknownValueError:
            # Se houver silêncio no bloco, ele ignora e pula pro próximo sem quebrar o loop
            continue
        except Exception as e:
            logger.error(f"Erro interno no loop de ditado: {e}")
            break
            
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        
    final_transcript = " ".join(full_text_blocks)
    logger.info(f"Ditado final unificado: {final_transcript}")
    return final_transcript

# ... (manter todo o conteúdo anterior até o final)

def listen(callback):
    """
    Orquestrador de escuta: Modo de Escuta Ativa (contínua).
    Removemos a dependência do wake_word para evitar erro de inicialização.
    """
    logger.info("Sistema de Voz: Escuta ativa iniciada (Aguardando comando)...")
    
    while True:
        # Pula a espera pelo 'JIMI' e vai direto para a captura
        comando = listen_command(timeout=5, phrase_limit=6)
        
        if comando:
            logger.info(f"Comando detectado: {comando}")
            callback(comando)
        
        # Pequeno delay para estabilidade de hardware
        import time
        time.sleep(1)