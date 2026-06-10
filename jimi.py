import threading
import traceback

# CORE
from core.planner import plan
from core.executor import execute
from core.security import is_safe

# MEMÓRIA
from memory.memory_manager import memory_manager

# VOZ
from voice.voice_engine import speak
from voice.audio_ai import listen

# WAKE WORD
from voice.wake_word import detect_wake_word, extract_command

# ================= ESTADO =================

RUNNING = True
ACTIVE_MODE = False

# ================= LOG =================

def log(*args):
    print("[JIMI]", *args)

# ================= PROCESSAMENTO CENTRAL =================

def process_input(user_input: str) -> str:
    try:
        # segurança
        if not is_safe(user_input):
            return "Esse comando não é permitido"

        # memória aprende
        memory_manager.extract_info(user_input)

        # planejamento
        action = plan(user_input)

        # execução
        if action:
            result = execute(action)
        else:
            result = "Ainda estou aprendendo isso"

        # salvar histórico
        memory_manager.add_interaction(user_input, result)

        return result

    except Exception as e:
        log("Erro crítico:", e)
        traceback.print_exc()
        return "Tive um erro interno"

# ================= CALLBACK DE VOZ =================

def on_speech(text: str):
    global ACTIVE_MODE

    if not text:
        return

    text = text.lower()
    log(f"Você disse: {text}")

    # WAKE WORD
    if detect_wake_word(text):
        ACTIVE_MODE = True
        speak("Sim?")
        return

    # ignora se não estiver ativo
    if not ACTIVE_MODE:
        return

    # desativar
    if any(cmd in text for cmd in ["parar", "fica quieto", "desativar", "silêncio"]):
        ACTIVE_MODE = False
        speak("Modo silencioso ativado")
        return

    # extrai comando
    command = extract_command(text)

    if not command:
        speak("Pode repetir?")
        return

    response = process_input(command)

    if response:
        speak(response)

# ================= MODO TEXTO =================

def cli_loop():
    global RUNNING

    print("💻 Modo texto ativo (digite 'sair' para encerrar)\n")

    while RUNNING:
        try:
            user_input = input("Você: ")

            if user_input.lower() in ["sair", "exit", "quit"]:
                shutdown()
                break

            response = process_input(user_input)

            print("Jimi:", response)
            speak(response)

        except Exception as e:
            log("Erro no CLI:", e)

# ================= VOZ =================

def start_voice():
    try:
        listen(on_speech_detected=on_speech)
    except Exception as e:
        log("Erro na voz:", e)

# ================= CONTROLE =================

def shutdown():
    global RUNNING
    RUNNING = False
    print("\n🛑 Encerrando JIMI...")

# ================= MAIN =================

def main():
    print("""
🤖 =========================
        JIMI ONLINE
=========================
Modo híbrido:
- Voz (wake word: Jimi)
- Texto simultâneo
=========================
""")

    # thread de voz
    voice_thread = threading.Thread(target=start_voice, daemon=True)
    voice_thread.start()

    # loop principal
    cli_loop()

# ================= RUN =================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        shutdown()