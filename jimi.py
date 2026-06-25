import os
import signal
import threading
import logging

# --- DETECÇÃO DE AMBIENTE ---
IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "")
IS_ANDROID = IS_TERMUX
IS_DESKTOP = os.name == "nt" or os.name == "posix" and not IS_TERMUX

# --- CONFIGURAÇÃO CENTRAL DE LOGS DO SISTEMA ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("jimi_system.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.getLogger().handlers[1].setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("JIMI.Main")

logger.info(f"[BOOT] Ambiente detectado: {'TERMUX' if IS_TERMUX else 'DESKTOP'}")

# --- IMPORTAÇÃO INTELIGENTE DO CÉREBRO ---
try:
    from core.brain import jimi_brain as brain
except ImportError:
    from brain import jimi_brain as brain

# --- SERVICES MANAGER ---
try:
    from services.services_manager import services_manager
except ImportError:
    logger.warning("[ALERTA] ServicesManager indisponível.")
    services_manager = None

# --- WEB SERVER ---
try:
    from interface.web_server import web_server
except ImportError as e:
    logger.warning(f"[ALERTA] WebServer indisponível: {e}")
    web_server = None

terminal_lock = threading.Lock()


class JimiSystem:
    def __init__(self):
        self.running = True
        self.voice_enabled = not IS_TERMUX  # 🔥 DESATIVA VOZ NO TERMUX

    def clear_terminal(self):
        if not IS_TERMUX:
            os.system('cls' if os.name == 'nt' else 'clear')

    def show_banner(self):
        banner = """
============================================================
██╗██╗███╗   ███╗██╗     ██████╗  ██████╗  ██████╗ ██████╗
============================================================
"""
        print(banner)

    def verify_modules(self):
        print("[*] Sincronizando subsistemas...")

        modules = {
            "Brain": "core.brain",
            "Planner": "core.planner",
            "Executor": "core.executor",
            "Services": "services.services_manager",
            "System": "services.system_service",
            "Voice": "services.voice_service"
        }

        for name, path in modules.items():
            try:
                __import__(path)
                print(f"  [✓] {name}: OK")
            except Exception as e:
                # MUDANÇA AQUI: Vamos imprimir o erro real
                print(f"  [X] {name}: OFF (Erro: {e})")
                import traceback
                traceback.print_exc() # Isso mostrará exatamente a linha que falhou

        print("\n[✓] Inicialização concluída\n")

    def start(self):
        self.clear_terminal()
        self.show_banner()
        self.verify_modules()

        # --- WEB SERVER (ESSENCIAL PARA iOS) ---
        if web_server:
            try:
                web_server.start()
                logger.info("[WEB] Servidor web iniciado com sucesso.")
            except Exception as e:
                logger.error(f"[WEB] Falha ao iniciar servidor: {e}")
        else:
            logger.warning("[WEB] Offline.")

        # --- VOZ (APENAS DESKTOP) ---
        if self.voice_enabled:
            voice_thread = threading.Thread(target=self._voice_listener_thread, daemon=True)
            voice_thread.start()
        else:
            logger.info("[VOICE] Desativado no Termux.")

        # --- CLI ---
        self._cli_loop()

    def _voice_listener_thread(self):
        try:
            if services_manager:
                from voice.audio_ai import listen
                listen(callback=self._handle_voice_input)
            else:
                logger.warning("[VOICE] ServicesManager offline.")
        except Exception as e:
            with terminal_lock:
                print(f"\n🛑 Erro áudio: {e}")

    def _handle_voice_input(self, text):
        if not text:
            return

        with terminal_lock:
            print(f"\n[Voz] > {text}")
            response = brain.think(text)
            print(f"JIMI (Voz) > {response}\n")

            if services_manager:
                try:
                    services_manager.execute_task("voice", "speak", response)
                except:
                    pass

    def _cli_loop(self):
        while self.running:
            try:
                user_input = input("Sr. Pedro > ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "sair", "shutdown"]:
                    self.shutdown()
                    break

                with terminal_lock:
                    print("JIMI > Pensando...", end="\r")
                    response = brain.think(user_input)

                    print(" " * 40, end="\r")
                    print(f"JIMI > {response}\n")

                    if services_manager and not IS_TERMUX:
                        try:
                            services_manager.execute_task("voice", "speak", response)
                        except:
                            pass

            except (KeyboardInterrupt, EOFError):
                self.shutdown()
                break

    def shutdown(self, signum=None, frame=None):
        self.running = False
        print("\n🛑 Encerrando JIMI com segurança.")
        sys.exit(0)


if __name__ == "__main__":
    jimi = JimiSystem()
    signal.signal(signal.SIGINT, jimi.shutdown)
    jimi.start()