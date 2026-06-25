import logging
import platform

logger = logging.getLogger("JIMI.SystemService")

# Gatekeeper 1: psutil (Monitoramento de Hardware)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil não instalado. Monitoramento de hardware desativado.")

# Gatekeeper 2: pygetwindow (Leitura de Janelas - Específico para Windows)
try:
    import pygetwindow as gw
    GW_AVAILABLE = True
except ImportError:
    GW_AVAILABLE = False
    logger.warning("pygetwindow não instalado. Leitura de janelas desativada.")


class SystemService:
    def __init__(self):
        self.os_type = platform.system().lower()

    def handle(self, action: str, payload=None):
        """Hub central de delegacao."""
        if action in ["get_context", "get_current_context"]:
            return self.get_current_context()
        if action == "get_usage":
            return self._get_hardware_telemetry()
        return f"Ação '{action}' não é suportada pelo módulo de Sistema."

    def _get_hardware_telemetry(self):
        """Retorna uso de CPU e RAM para o JIMI saber se está 'cansado'."""
        # O Guarda de Proteção do psutil
        if not PSUTIL_AVAILABLE:
            return {
                "cpu_percent": 0,
                "ram_percent": 0
            }
        
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "ram_percent": psutil.virtual_memory().percent
            }
        except Exception as e:
            logger.error(f"Erro ao ler telemetria: {e}")
            return {"cpu_percent": 0, "ram_percent": 0}

    def get_current_context(self) -> dict:
        """Coleta contexto de software e hardware."""
        logger.info("Mapeando estado do sistema...")
        
        # Hardware
        telemetry = self._get_hardware_telemetry()
        
        # Software (Contexto de Janelas)
        window_title = "Desktop"
        
        # O Guarda de Proteção do pygetwindow garante que só execute no Windows
        # E somente se a biblioteca foi importada com sucesso
        if self.os_type == "windows" and GW_AVAILABLE:
            try:
                # Tenta pegar a janela ativa real
                win = gw.getActiveWindow()
                if win:
                    window_title = win.title
            except Exception:
                pass

        context = {
            "active_window": window_title,
            "status": "indeterminado",
            "project_name": "Nenhum",
            "listening_to": None,
            "cpu": telemetry["cpu_percent"],
            "ram": telemetry["ram_percent"]
        }

        # Lógica de inferência (Inteligência de Estado)
        w_lower = window_title.lower()
        
        # Estados de Trabalho
        if any(x in w_lower for x in ["visual studio code", "vs code", "pycharm"]):
            context["status"] = "trabalhando"
            context["project_name"] = window_title.split("-")[0].strip()
        elif "uninter" in w_lower:
            context["status"] = "estudando"
        elif any(x in w_lower for x in ["spotify", "youtube", "deezer"]):
            context["listening_to"] = window_title.split("-")[0].strip()
            context["status"] = "consumindo mídia"

        # Adiciona inteligência de carga: Se CPU > 80%, o JIMI deve ser breve nas respostas
        # Como o fallback de erro retorna 0, esta matemática não vai quebrar o código
        if telemetry["cpu_percent"] > 80:
            context["status"] += " (sistema sob alta carga)"

        return context

system_service = SystemService()