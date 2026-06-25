import logging
from services.services_manager import services_manager

# --- ISOLAMENTO DE IMPORTS EM CAMADAS DEFENSIVAS ---
# Mantemos apenas o que é estritamente necessário para a tomada de decisão do executor
try:
    from memory.memory_manager import memory_manager
    from core.security import security_manager
except Exception as e:
    logging.error(f"[EXECUTOR] Módulos auxiliares de segurança/memória offline: {e}")
    memory_manager = None
    security_manager = None

logger = logging.getLogger("JIMI.Executor")

def execute(action: dict):
    """
    O Executor agora foca apenas em: Validar Segurança -> Registrar na Memória -> Delegar ao Hub.
    """
    if not action or "type" not in action:
        return "Comando inválido."

    action_type = action.get("type")
    value = action.get("value")
    meta = action.get("meta", {})

    # 1. Auditoria de Segurança
    if security_manager and not security_manager.is_safe(f"{action_type}:{value}").get("safe", False):
        return "Protocolo de segurança: Ação não autorizada."

# 2. Execução (Delegando ao Hub de Serviços ou Motor de Build)
    logger.info(f"[EXECUTOR] Despachando diretiva: {action_type} | Valor: {value}")

    try:
        # --- NOVO: Roteamento para o BuilderEngine ---
        if action_type == "build_task":
            from core.builder_engine import builder_engine
            return builder_engine.add_task(task_name=value, meta=meta)
            
        # --- MANTIDO: Roteamento original para hardware/serviços ---
        payload = {"value": value, "meta": meta}
        result = services_manager.execute_task(action_type, action_name=value, payload=payload)
        
        # 3. Registro na Memória (Opcional, mas recomendado)
        if memory_manager:
            memory_manager.register_action(action_type, {"value": value, "result": result})
            
        return result

    except Exception as e:
        logger.error(f"[EXECUTOR] Falha crítica na execução de {action_type}: {e}")
        return f"Erro técnico ao processar: {e}"