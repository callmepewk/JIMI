# services/voice_service.py
import logging
import os


# Importações direcionadas para a sua estrutura da pasta 'voice'
try:
    from voice.voice_engine import voice_engine
except ImportError:
    # Fallback caso sua classe interna em voice_engine tenha outro nome
    voice_engine = None

logger = logging.getLogger("JIMI.VoiceService")

class VoiceService:
    def __init__(self):
        # Utiliza a sua engine que já está configurada na pasta voice
        self.engine = voice_engine
        if not self.engine:
            logger.warning("Aviso: 'voice_engine' não pôde ser importado da pasta 'voice/'. Modo texto ativado.")

    def handle(self, action: str, payload=None):
        """
        Ponto de entrada unificado para o ServicesManager do JIMI.
        """
        if action == "speak":
            if payload:
                return self.speak(str(payload))
            return "Erro: Nenhum texto fornecido para a ação de fala."
            
        elif action == "listen_reply":
            return self.listen_for_confirmation()
            
        return f"Ação '{action}' não é suportada pelo módulo de Voz."

    def speak(self, text: str) -> str:
        """
        Invoca a engine de áudio local para ler um aviso para você em voz alta.
        """
        logger.info(f"[TTS Executando]: \"{text}\"")
        if self.engine and hasattr(self.engine, 'speak'):
            try:
                # Chama o método de fala da sua própria engine
                self.engine.speak(text)
                return "Áudio sintetizado e reproduzido."
            except Exception as e:
                logger.error(f"Erro ao interagir com a voice_engine: {e}")
                return f"Falha na reprodução de áudio: {e}"
        else:
            # Fallback seguro caso o hardware ou arquivo de áudio falhe
            print(f"\n📢 [JIMI EM VOZ ALTA]: {text}\n")
            return "Reproduzido via fallback de console."

    def listen_for_confirmation(self) -> dict:
        """
        Ativa temporariamente a captura do microfone para ouvir um comando rápido de voz.
        Retorna um dicionário com o status da transcrição.
        """
        logger.info("Iniciando escuta ativa para resposta de voz do usuário...")
        
        # Aqui faremos a ponte com sua lógica de STT ou wake_word.py se necessário.
        # Por hora, ele captura e valida strings básicas para o fluxo do WhatsApp.
        try:
            # Caso você queira embutir o SpeechRecognition diretamente aqui:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                logger.info("Microfone aberto... Pode falar agora.")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
                
                text_transcribed = recognizer.recognize_google(audio, language="pt-BR").lower()
                logger.info(f"Transcrição capturada: '{text_transcribed}'")
                
                return {
                    "success": True,
                    "text": text_transcribed,
                    "confirmed": "sim" in text_transcribed or "responde" in text_transcribed
                }
        except Exception as e:
            logger.warning(f"Não foi possível capturar resposta via áudio (Microfone ocupado ou timeout): {e}")
            return {"success": False, "text": "", "confirmed": False}


# Instanciação global para o barramento do ServicesManager
voice_service = VoiceService()