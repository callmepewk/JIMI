"""
Interface de alto nível para o sistema de voz do JIMI.
Redireciona as chamadas para o motor central (voice_engine).
"""
from voice_engine import speak as engine_speak, stop as engine_stop, is_busy as engine_is_busy

def speak(text, interrupt=False):
    """
    Função principal para o JIMI falar.
    :param text: O texto a ser falado.
    :param interrupt: Se True, interrompe a fala atual antes de começar a próxima.
    """
    engine_speak(text, interrupt=interrupt)

def stop():
    """Interrompe a fala atual do JIMI imediatamente."""
    engine_stop()

def is_speaking():
    """Retorna True se o JIMI estiver falando no momento."""
    return engine_is_busy()