import socket
import subprocess
import platform
import requests
import logging

logger = logging.getLogger("JIMI.NetworkService")

class NetworkService:
    def handle(self, action: str, payload=None):
        """
        Ponto de entrada unificado para o ServicesManager do JIMI.
        Gerencia o diagnóstico de conexões, IPs e pings.
        """
        if action == "ping":
            host = str(payload) if payload else "8.8.8.8"
            return self.ping_host(host)
            
        elif action == "check":
            online = self.check_internet()
            return "Conexão com a internet ativa e estável." if online else "A máquina está completamente offline."
            
        elif action == "local_ip":
            return f"IP Local da máquina: {self.get_local_ip()}"
            
        elif action == "public_ip":
            return f"IP Público da conexão: {self.get_public_ip()}"
            
        elif action == "status":
            # Retorna um diagnóstico completo estruturado
            return {
                "internet_active": self.check_internet(),
                "local_ip": self.get_local_ip(),
                "public_ip": self.get_public_ip()
            }

        return f"Ação '{action}' não é suportada pelo módulo de Rede."

    def check_internet(self) -> bool:
        """Verifica se há conexão ativa com a internet batendo num DNS público."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def get_local_ip(self) -> str:
        """Retorna o IP local da máquina na sua rede Wi-Fi/Ethernet."""
        try:
            s = socket.socket(socket.AF_INET, socket.socket.SOCK_DGRAM if hasattr(socket, "SOCK_DGRAM") else socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def get_public_ip(self) -> str:
        """Descobre o IP público da sua conexão de internet."""
        try:
            return requests.get("https://api.ipify.org", timeout=3).text
        except Exception:
            return "Desconectado"

    def ping_host(self, host="8.8.8.8") -> str:
        """Mede a latência (ping) com um servidor externo."""
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "1", host]
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
            if "ms" in output or "ttl" in output.lower():
                return f"Ping estável. Conexão ativa com {host}."
            return "Host alcançado, mas sem resposta de eco padrão."
        except Exception:
            return f"Falha ao pingar o host {host}."


# Instanciação global necessária para o circuito do ServicesManager
network_service = NetworkService()