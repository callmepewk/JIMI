import os
import re
import sys
import time
import json
import hashlib
import logging
import subprocess
import threading

logger = logging.getLogger("JIMI.Security")

class SecurityManager:
    def __init__(self):
        # 1. IPs Permitidos (Sua Rede Local e Interfaces Conhecidas)
        self.ALLOWED_IPS = ["127.0.0.1", "localhost"] 
        # Nota: IPs dinâmicos de redes móveis (4G/5G) serão validados via Token Criptográfico + MFA
        
        # 2. Usuários Autores Autorizados para Modificação de Código no GitHub
        self.AUTHORIZED_COMMITTERS = ["Pedro Henrique Brezolin de Freitas", "self_evolution", "jimi-builder-bot"]

        # 3. Bloqueio por Regex Destrutivo (Blacklist Estrita)
        self.BLOCK_PATTERNS = [
            r"rm\s*-rf", r"formatar\s*c:", r"deletar\s*sistema", 
            r"apagar\s*tudo", r"sudo\s+rm", r"drop\s+database", 
            r"fdisk", r"del\s*/f/s/q\s*c:\\", r"powershell\s+iex",
            r"mkfs", r"shutdown\s+/s", r"> /dev/s"
        ]
        
        # 4. Whitelist de Escopos Operacionais Seguros
        self.ALLOWED_ACTIONS = [
            "open_url", "open_app", "automation", "camera", 
            "system", "voice", "network_check", "maps", 
            "whatsapp", "email", "chat", "wake_on_lan"
        ]

        # Estado do Sistema de Quarentena e Lock de Arquivos
        self.lockdown_active = False
        self.mfa_queue = {}
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Inicializa o monitoramento de integridade do código em Thread separada
        threading.Thread(target=self._watchdog_integridade_repositorio, daemon=True, name="JIMI-Watchdog").start()

    def _sanitize(self, text: str) -> str:
        """Remove caracteres perigosos de encadeamento de comandos de terminal."""
        if not text:
            return ""
        return re.sub(r'[;&|`$]', '', text)

    def verify_ip(self, ip_origem: str) -> bool:
        """Valida se o IP de origem pertence à infraestrutura autorizada."""
        if ip_origem in self.ALLOWED_IPS or ip_origem.startswith("1192.168.") or ip_origem.startswith("10."):
            return True
        logger.warning(f"Origem externa desconhecida detectada: {ip_origem}. Passando para validação secundária por Token.")
        return False

    def is_safe(self, action_payload: str, ip_origem: str = "127.0.0.1") -> dict:
        """Avalia a segurança lógica e estrutural do comando recebido."""
        if self.lockdown_active:
            return {"safe": False, "reason": "SISTEMA EM LOCKDOWN. Comandos suspensos para segurança.", "level": "CRITICAL"}

        safe_text = self._sanitize(action_payload.lower().strip())

        # 1. Verificação Cega na Blacklist Destrutiva
        for pattern in self.BLOCK_PATTERNS:
            if re.search(pattern, safe_text):
                logger.critical(f"ALERTA EXTREMO: Tentativa de injeção destrutiva bloqueada: {safe_text}")
                self.trigger_lockdown("Tentativa de execucao de comando destrutivo via API externa.")
                return {"safe": False, "reason": "Comando permanentemente banido da arquitetura.", "level": "CRITICAL"}

        # 2. Validação contra a Whitelist Funcional
        action_type = safe_text.split(':')[0] if ':' in safe_text else safe_text
        if action_type not in self.ALLOWED_ACTIONS and action_type != "system_cmd":
            logger.warning(f"Comando fora do escopo padrao interceptado: '{action_type}'. Movendo para quarentena MFA.")
            return {"safe": False, "need_mfa": True, "reason": "Acao requer autorizacao explicita do Sr. Pedro.", "level": "WARN"}

        return {"safe": True, "reason": "Comando em conformidade técnica.", "level": "USER"}

    def criar_solicitacao_mfa(self, command_id: str, payload: dict) -> str:
        """Gera uma entrada na fila de aprovação pendente para o iOS."""
        self.mfa_queue[command_id] = {
            "payload": payload,
            "timestamp": time.time(),
            "status": "pending"
        }
        logger.info(f"MFA [{command_id}] gerado. Aguardando liberacao manual via iOS/Notificacao.")
        return f"Aguardando confirmacao multifator para a acao {command_id}."

    def responder_mfa(self, command_id: str, aprovado: bool) -> bool:
        """Libera ou expurga o comando retido em quarentena com base na sua ação no iOS."""
        if command_id in self.mfa_queue:
            if aprovado:
                self.mfa_queue[command_id]["status"] = "approved"
                logger.info(f"MFA [{command_id}] APROVADO pelo usuario. Executando carga...")
                return True
            else:
                logger.warning(f"MFA [{command_id}] REJEITADO/BLOQUEADO pelo usuario. Excluindo rastro.")
                del self.mfa_queue[command_id]
        return False

    def trigger_lockdown(self, motivo: str):
        """Corta todas as comunicações externas e isola a execução da IA."""
        self.lockdown_active = True
        logger.critical(f"!!! DISPARANDO PROTOCOLO LOCKDOWN INTERNO !!! Motivo: {motivo}")
        # Aqui o JIMI pode disparar um sinal direto de voz no Moto G7 avisando sobre a invasão
        try:
            from voice.voice_engine import speak
            speak("Aviso de segurança. Tentativa de invasão detectada. Isolando subsistemas locais.", interrupt=True)
        except Exception:
            pass

    def _watchdog_integridade_repositorio(self):
        """Monitor de integridade ativo. Executa a cada 60 segundos buscando alterações hostis no Git."""
        logger.info("Watchdog de integridade do código-fonte ativado.")
        while True:
            try:
                if os.path.exists(os.path.join(self.root_dir, ".git")):
                    # Captura quem realizou o último commit local/remoto
                    resultado_autor = subprocess.run(
                        ["git", "log", "-1", "--format=%an"], 
                        cwd=self.root_dir, capture_output=True, text=True, check=True
                    )
                    ultimo_autor = resultado_autor.stdout.strip()

                    # Verifica se o autor do código é uma entidade confiável
                    if ultimo_autor and ultimo_autor not in self.AUTHORIZED_COMMITTERS:
                        logger.critical(f"FRAUDE DE REPOSITORIO DETECTADA! Codigo alterado por usuario nao-autorizado: '{ultimo_autor}'")
                        
                        # Ação Corretiva Autônoma: Exclui as alterações hostis e resgata a versão limpa do Dono
                        logger.warning("Executando reversao autonoma de infraestrutura para salvaguardar o nucleo...")
                        subprocess.run(["git", "clean", "-fd"], cwd=self.root_dir, capture_output=True)
                        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=self.root_dir, capture_output=True)
                        
                        self.trigger_lockdown(f"Codigo corrompido por autor hostil externo: {ultimo_autor}")
                    
                    # Verifica se existem modificações locais não rastreadas (arquivos alterados sem passar por commit)
                    status_git = subprocess.run(
                        ["git", "status", "--porcelain"], 
                        cwd=self.root_dir, capture_output=True, text=True, check=True
                    )
                    if status_git.stdout.strip() and "tunnel_url.txt" not in status_git.stdout and "token.json" not in status_git.stdout:
                        # Se houver modificações em arquivos de sistema (.py) que não foram feitas pelo bot ou por você
                        logger.warning("Modificacoes nao controladas em arquivos do Core detectadas fora de escopo controlado.")
                        
            except Exception as e:
                logger.error(f"Erro no ciclo de checagem do Watchdog de Seguranca: {e}")
                
            time.sleep(60) # Intervalo padrão de varredura de integridade

# Instância unificada de proteção de borda
security_manager = SecurityManager()