import json
import logging
from datetime import datetime
from jimi.automation import execute_action
from jimi.memory_manager import memory_manager
from jimi.planner import planner
from jimi.executor import execute

# Configuração de Logs Profissional
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JIMI.Brain")

class Brain:
    def __init__(self):
        self.memory = memory_manager
        self.planner = planner

    def _get_system_context(self):
        """Prepara o estado atual do sistema para a LLM."""
        return {
            "time": datetime.now().strftime("%H:%M"),
            "memory": self.memory.get_ai_context(),
            "status": "online"
        }

    def think(self, user_input):
        logger.info(f"Processando: {user_input}")
        
        # 1. Registro de Memória Curta
        self.memory.extract_info(user_input)

        # 2. Tentativa de Ação Determinística (Flash Response)
        # Se for uma ação direta, o planejador identifica e o executor roda imediatamente.
        plan = self.planner.plan(user_input)
        
        if plan and plan["type"] != "chat":
            logger.info(f"Plano identificado: {plan}")
            result = execute(plan)
            self.memory.add_interaction(user_input, result)
            return result

        # 3. Processamento Cognitivo (LLM)
        # Se não for uma ação direta, o JIMI "pensa" sobre o contexto.
        response = self._generate_thoughtful_response(user_input)
        
        self.memory.add_interaction(user_input, response)
        return response

    def _generate_thoughtful_response(self, user_input):
        context = self._get_system_context()
        # Aqui o prompt é enriquecido com a memória semântica que construímos
        prompt = f"Contexto: {context}. Usuário: {user_input}. Responda como Jarvis."
        
        # Chamada ao seu motor de LLM (Ollama)
        # response = ask_llm(prompt) 
        return "Compreendido, Sr. Pedro. Analisando a solicitação..."

# Instância única para o Sistema
brain = Brain()