import re
import logging

class SecurityManager:
    def __init__(self):
        # Regex para capturar variações e evitar bypass
        self.BLOCK_PATTERNS = [
            r"rm\s*-rf",
            r"formatar\s*c:",
            r"deletar\s*sistema",
            r"apagar\s*tudo",
            r"sudo\s+rm",
            r"drop\s+database",
            r"fdisk"
        ]
        
        # Comandos que exigem confirmação humana (Nível de Autorização 2)
        self.REQUIRES_AUTH = [
            r"desligar",
            r"reiniciar",
            r"encerrar\s*processos"
        ]

    def is_safe(self, text: str) -> dict:
        """
        Retorna status de segurança e o nível de risco.
        Retorna: {"safe": bool, "reason": str, "level": str}
        """
        text = text.lower().strip()

        # 1. Verificação de Bloqueio Total (Nível Crítico)
        for pattern in self.BLOCK_PATTERNS:
            if re.search(pattern, text):
                logging.warning(f"Tentativa de comando malicioso bloqueada: {text}")
                return {"safe": False, "reason": "Comando proibido detectado.", "level": "CRITICAL"}

        # 2. Verificação de Autorização (Nível Administrativo)
        for pattern in self.REQUIRES_AUTH:
            if re.search(pattern, text):
                return {"safe": True, "reason": "Requer autorização humana.", "level": "ADMIN"}

        return {"safe": True, "reason": "Comando seguro.", "level": "USER"}

# Instância única
security_manager = SecurityManager()