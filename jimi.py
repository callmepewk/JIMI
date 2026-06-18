import os
import sys
import signal
import threading
import logging

# --- CONFIGURAÇÃO CENTRAL DE LOGS DO SISTEMA ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("jimi_system.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
# Reduz o nível de logs para o console para não poluir o terminal interativo
logging.getLogger().handlers[1].setLevel(logging.WARNING)

# Silencia logs repetitivos de conexões HTTP para manter o terminal limpo
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("JIMI.Main")

# --- IMPORTAÇÃO INTELIGENTE DO CÉREBRO COGNITIVO ---
try:
    from core.brain import jimi_brain as brain
except ImportError:
    from brain import jimi_brain as brain

# --- HUB CENTRAL DE HARDWARE E SERVIÇOS ---
try:
    from services.services_manager import services_manager
except ImportError:
    logger.error("[CRÍTICO] Não foi possível carregar o ServicesManager. Módulos físicos offline.")
    services_manager = None

# --- PORTAL DE COMUNICAÇÃO WEB (FLASK SERVER) ---
try:
    from interface.web_server import web_server
except ImportError as e:
    logger.error(f"[CRÍTICO] Não foi possível carregar o Portal Web: {e}")
    web_server = None

# Garante sincronia visual no terminal entre Threads diferentes
terminal_lock = threading.Lock()


class JimiSystem:
    def __init__(self):
        self.running = True

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_banner(self):
        banner = """
    ============================================================
       ██╗██╗███╗   ███╗██╗     ██████╗  ██████╗  ██████╗ ██████╗ 
       ██║██║████╗ ████║██║    ██╔════╝ ██╔═══██╗██╔════╝ ██╔═══██╗
       ██║██║██╔████╔██║██║    ██║  ███╗██║   ██║██║  ███╗██║   ██║
  ██   ██║██║██║╚██╔╝██║██║    ██║   ██║██║   ██║██║   ██║██║   ██║
  ╚█████╔╝██║██║ ╚═╝ ██║██║    ╚██████╔╝╚██████╔╝╚██████╔╝██████╔╝
   ╚════╝ ╚═╝╚═╝     ╚═╝╚═╝     ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝ 
    ------------------------------------------------------------
           SISTEMA OPERACIONAL ASSISTENTE DE ALTO NÍVEL
           DESENVOLVEDOR: SR. PEDRO HENRIQUE B. DE FREITAS
    ============================================================
        """
        print(banner)

    def verify_modules(self):
        print("[*] Sincronizando subsistemas físicos, neurais e de voz...")
        
        # Mapeamento de caminhos para checagem rápida no boot do sistema
        modules = {
            "Cérebro Cognitivo (Brain)": "core.brain" if "core.brain" in sys.modules else "brain",
            "Triador de Intenções (Planner)": "core.planner",
            "Executor de Hardware (Executor)": "core.executor",
            "Gerenciador de Serviços (Hub)": "services.services_manager",
            "Módulo de Sistema (Contexto)": "services.system_service",
            "Módulo de Voz (Wrapper)": "services.voice_service"
        }
        
        for name, path in modules.items():
            try:
                __import__(path)
                print(f"  [✓] {name}: ONLINE")
            except Exception as e:
                print(f"  [X] {name}: FALHOU OU FORA DE LINHA ({e})")
                
        print("\n[✓] Canais de comunicação estabilizados. Inicializando interfaces...\n")

    def start(self):
        self.clear_terminal()
        self.show_banner()
        self.verify_modules()
        
        # 1. Iniciar o Servidor Web para acesso via Celular / Cloudflare Tunnel
        if web_server:
            web_server.start()
        else:
            logger.warning("[ALERTA] Servidor Web offline. Acesso remoto indisponível.")
            
        # 2. Dispara a Thread de captação de voz local (Microfone do PC)
        voice_thread = threading.Thread(target=self._voice_listener_thread, daemon=True)
        voice_thread.start()
        
        # 3. Inicia o loop interativo via terminal (Console)
        self._cli_loop()

    def _voice_listener_thread(self):
        """Monitora continuamente o ambiente de áudio em segundo plano."""
        try:
            if services_manager:
                from voice.audio_ai import listen
                listen(callback=self._handle_voice_input)
            else:
                logger.error("Driver de áudio não inicializado: ServicesManager offline.")
        except Exception as e:
            with terminal_lock:
                print(f"\n🛑 [ALERTA] Falha crítica no barramento do driver de áudio: {e}")

    def _handle_voice_input(self, text):
        """Ponte assíncrona protegida entre o microfone e o processador cognitivo."""
        if not text: 
            return
        
        with terminal_lock:
            print(f"\n[Voz Detectada] > {text}")
            print("JIMI > Processando comando de voz...", end="\r")
            
            response = brain.think(text)
            
            print(" " * 40, end="\r")
            print(f"JIMI (Voz) > {response}\n")
            
            if services_manager:
                services_manager.execute_task("voice", "speak", response)
            print("Sr. Pedro > ", end="", flush=True)

    def _cli_loop(self):
        while self.running:
            try:
                user_input = input("Sr. Pedro > ").strip()
                if not user_input:
                    continue
                    
                if user_input.lower() in ["sair", "exit", "shutdown", "fechar"]:
                    self.shutdown()
                    break
                
                with terminal_lock:
                    print("JIMI > Pensando...", end="\r")
                    response = brain.think(user_input)
                    
                    print(" " * 40, end="\r")
                    print(f"JIMI > {response}\n")
                    
                    if services_manager:
                        services_manager.execute_task("voice", "speak", response)
                
            except (KeyboardInterrupt, EOFError):
                self.shutdown()
                break

    def shutdown(self, signum=None, frame=None):
        self.running = False
        print("\n\n🛑 [SISTEMA] Desativando protocolos físicos e deslogando JIMI com segurança.")
        sys.exit(0)


if __name__ == "__main__":
    jimi = JimiSystem()
    signal.signal(signal.SIGINT, jimi.shutdown)
    jimi.start()