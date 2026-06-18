import pygetwindow as gw
import psutil
import logging
import platform

logger = logging.getLogger("JIMI.SystemService")

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
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent
        }

    def get_current_context(self) -> dict:
        """Coleta contexto de software e hardware."""
        logger.info("Mapeando estado do sistema...")
        
        # Hardware
        telemetry = self._get_hardware_telemetry()
        
        # Software (Contexto de Janelas)
        window_title = "Desktop"
        if self.os_type == "windows":
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
        if telemetry["cpu_percent"] > 80:
            context["status"] += " (sistema sob alta carga)"

        return context

system_service = SystemService()