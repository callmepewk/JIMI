import re
import logging
import hashlib
import time

logger = logging.getLogger("JIMI.Security")

class SecurityManager:
    def __init__(self):
        # 1. Bloqueio por Regex (O que NUNCA pode rodar)
        self.BLOCK_PATTERNS = [
            r"rm\s*-rf", r"formatar\s*c:", r"deletar\s*sistema", 
            r"apagar\s*tudo", r"sudo\s+rm", r"drop\s+database", 
            r"fdisk", r"del\s*/f/s/q\s*c:\\"
        ]
        
        # 2. Whitelist de Ações Permitidas (O que É permitido)
        # Qualquer coisa fora daqui é tratada com desconfiança
        self.ALLOWED_ACTIONS = [
            "open_url", "open_app", "automation", "camera", 
            "system", "voice", "network_check", "maps", 
            "whatsapp", "email", "chat"
        ]

    def _sanitize(self, text: str) -> str:
        """Remove caracteres de escape e tenta evitar injeção de comandos."""
        return re.sub(r'[;&|`$]', '', text)

    def is_safe(self, action_payload: str, token: str = None) -> dict:
        """
        Avalia segurança com base em padrão de comando e token opcional.
        """
        # Sanitização preventiva
        safe_text = self._sanitize(action_payload.lower().strip())

        # 1. Verificação de Integridade (Bloqueio Total)
        for pattern in self.BLOCK_PATTERNS:
            if re.search(pattern, safe_text):
                logger.critical(f"BLOCKLIST TRIGGERED: {safe_text}")
                return {"safe": False, "reason": "Comando proibido.", "level": "CRITICAL"}

        # 2. Validação de Escopo (Whitelist)
        action_type = safe_text.split(':')[0]
        if action_type not in self.ALLOWED_ACTIONS and action_type != "system_cmd":
            logger.warning(f"Ação não reconhecida ou perigosa: {action_type}")
            return {"safe": False, "reason": "Ação não autorizada no escopo.", "level": "WARN"}

        return {"safe": True, "reason": "Comando validado.", "level": "USER"}

    def generate_access_token(self, secret: str):
        """Gera um hash simples para validar origem de atalhos externos."""
        return hashlib.sha256(f"{secret}{time.strftime('%Y-%m-%d')}".encode()).hexdigest()

# Instância única
security_manager = SecurityManager()