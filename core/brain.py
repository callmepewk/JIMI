import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger("JIMI.Brain")

# --- ISOLAMENTO DE IMPORTS CRÍTICOS ---
try:
    from memory.memory_manager import memory_manager
except Exception as e:
    logger.error(f"[FALLBACK] Erro ao carregar memory_manager: {e}")
    memory_manager = None

try:
    from core.planner import planner
except Exception as e:
    logger.error(f"[FALLBACK] Erro ao carregar planner: {e}")
    planner = None

try:
    from core.executor import execute
except Exception as e:
    logger.error(f"[FALLBACK] Erro ao carregar executor: {e}")
    execute = None

# --- CONEXÃO COM HUB DE SERVIÇOS PARA CONTEXTO DE TELA/MÍDIA ---
try:
    from services.services_manager import services_manager
except Exception as e:
    logger.error(f"[FALLBACK] ServicesManager inacessível pelo Brain: {e}")
    services_manager = None


class Brain:
    def __init__(self):
        self.memory = memory_manager
        self.planner = planner
        self.ollama_model = "llama3" 
        self.ollama_url = "http://127.0.0.1:11434/api/generate"

    def _get_system_context(self):
        """Prepara o estado atual do sistema, hardware e atividades para a LLM."""
        ai_context = "Módulo de memória local offline ou sem registros."
        
        if self.memory:
            try:
                raw_context = self.memory.get_ai_context()
                relevant_facts = raw_context.get("relevant_facts", [])
                facts_str = ", ".join(relevant_facts) if relevant_facts else "Nenhum fato histórico recente registrado."
                ai_context = f"Fatos da memória: {facts_str} | Última playlist: {raw_context.get('last_playlist', 'Nenhuma')}"
            except Exception as e:
                logger.error(f"Falha ao recuperar contexto da memória: {e}")

        # --- NOVA CAPTURA DE TELEMETRIA EM TEMPO REAL ---
        user_activity = "Status da atividade em tempo real indisponível."
        if services_manager:
            try:
                # Puxa dinamicamente as janelas abertas e mídias do Pedro via SystemService
                os_context = services_manager.execute_task("system", "get_current_context")
                if isinstance(os_context, dict):
                    user_activity = f"Janela ativa: '{os_context.get('active_window')}'. Atividade deduzida: {os_context.get('status')}."
                    if os_context.get("listening_to"):
                        user_activity += f" Consumindo mídia/música: '{os_context.get('listening_to')}'."
            except Exception as e:
                logger.debug(f"Falha leve ao injetar telemetria do SO no prompt: {e}")

        return {
            "date": datetime.now().strftime("%d/%m/%Y"),
            "time": datetime.now().strftime("%H:%M"),
            "memory": ai_context,
            "activity": user_activity,
            "status": "Operando em capacidade máxima"
        }

    def think(self, user_input: str) -> str:
        logger.info(f"Processando entrada cognitiva: '{user_input}'")
        
        # 1. Registro e extração semântica em memória curta
        if self.memory:
            try:
                self.memory.extract_info(user_input)
            except Exception as e:
                logger.error(f"Erro na etapa de extração de memória: {e}")

        # 2. Curto-Circuito Determinístico (Planner -> Executor)
        if self.planner and execute:
            try:
                plan = self.planner.plan(user_input)
                if plan and plan.get("type") != "chat":
                    logger.info(f"[BRAIN] Encaminhando plano para o Executor físico: {plan}")
                    result = execute(plan)
                    
                    if self.memory:
                        self.memory.add_interaction(user_input, f"[Ação Executada] {result}")
                    return result
            except Exception as e:
                logger.error(f"Erro ao tentar planejar/executar comando direto: {e}")

        # 3. Processamento Generativo via Ollama (Caso o comando seja conversacional)
        response = self._generate_thoughtful_response(user_input)
        
        if self.memory:
            try:
                self.memory.add_interaction(user_input, response)
            except Exception as e:
                logger.error(f"Erro ao salvar a interação na memória: {e}")
            
        return response

    def _generate_thoughtful_response(self, user_input: str) -> str:
        context = self._get_system_context()
        
        # Prompt de Identidade de alta fidelidade atualizado com telemetria
        prompt = (
            f"Você é o JIMI, um assistente virtual ultra-inteligente, focado, altamente eficaz, "
            f"sofisticado e cibernético, construído para apoiar e otimizar a rotina do seu criador.\n"
            f"Instruções obrigatórias de comportamento:\n"
            f"- Responda SEMPRE em português.\n"
            f"- Seja refinado, assertivo, prestativo e trate o usuário estritamente como 'Sr. Pedro'.\n"
            f"- Mantenha suas respostas diretas, evitando textos longos ou redundantes, a menos que solicitado.\n\n"
            f"Ambiente operacional:\n"
            f"- Data Atual: {context['date']}\n"
            f"- Horário Local: {context['time']}\n"
            f"- Status do Núcleo: {context['status']}\n"
            f"- Telemetria do Criador: {context['activity']}\n"
            f"- {context['memory']}\n\n"
            f"Mensagem do Sr. Pedro: {user_input}\n"
            f"Resposta do JIMI:"
        )
        
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            logger.info(f"Conectando ao motor Ollama ({self.ollama_model})...")
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            response.raise_for_status() 
            
            data = response.json()
            return data.get("response", "Erro: Resposta vazia gerada pelos módulos cognitivos.").strip()
            
        except requests.exceptions.HTTPError as http_e:
            logger.error(f"Erro HTTP no barramento do Ollama: {http_e}")
            return f"Sr. Pedro, meu motor cognitivo retornou um erro de comunicação (HTTP {response.status_code})."
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama inacessível na porta 11434: {e}")
            return "Compreendido, Sr. Pedro. No momento, meu motor cognitivo central local (Ollama) está offline."


# Instância global para importação simplificada
jimi_brain = Brain()