import subprocess
import webbrowser
import logging
from automation.automation import run_automation
from memory.memory_manager import memory_manager
from security.security_manager import security_manager

# Configuração de log para auditoria (Essencial para Jarvis)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JIMI.Executor")

def execute(action: dict):
    """
    Executor de alto nível com validação de segurança e auditoria.
    """
    if not action or "type" not in action:
        return "Comando inválido."

    action_type = action.get("type")
    value = action.get("value")
    meta = action.get("meta", {})

    # 1. Auditoria e Segurança (Camada Vital)
    # Verificamos se a ação proposta é segura antes de tocar no sistema
    security_check = security_manager.is_safe(f"{action_type}:{value}")
    if not security_check["safe"]:
        logger.error(f"Execução bloqueada: {action_type} - {value}")
        return "Protocolo de segurança: Ação não autorizada."

    try:
        logger.info(f"Executando: {action_type} | Valor: {value}")

        if action_type == "open_url":
            webbrowser.open(value)
            memory_manager.register_action("open_url", {"url": value})
            return f"Abrindo {value.split('//')[-1]}"

        elif action_type == "open_app":
            # Uso de lista para evitar shell=True (Mais seguro)
            subprocess.Popen([value], shell=False) 
            memory_manager.register_action("open_app", {"app": value})
            return f"Iniciando {value}"

        elif action_type == "automation":
            # O Executor delega a lógica complexa para o módulo de automação
            result = run_automation(value, meta)
            memory_manager.register_action("automation", {"name": value})
            return result

        elif action_type == "system":
            # Comando de sistema requer log detalhado
            subprocess.run(value, shell=True, check=True)
            memory_manager.register_action("system_cmd", {"cmd": value})
            return "Comando de sistema concluído."

        else:
            return f"Tipo de ação {action_type} não implementado."

    except Exception as e:
        logger.error(f"Falha na execução: {e}")
        return "Houve um erro técnico ao processar a solicitação."