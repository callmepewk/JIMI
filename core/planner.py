import logging
import re

# Configuração de log do Planejador Cógnito
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JIMI.Planner")

class Planner:
    def __init__(self):
        # Mapeamento expandido de intenções (Intenção -> Gatilhos textuais)
        self.intents = {
            "web_navigation": ["abrir", "navegar", "acessar", "site", "url"],
            "app_control": ["executar", "abrir aplicativo", "rodar", "iniciar"],
            "system": ["desligar", "reiniciar", "suspender", "apagar pc"],
            "automation": ["modo trabalho", "modo foco", "configurar ambiente"],
            "self_evolution": ["evolua", "melhore", "atualize", "modifique", "reescreva", "altere"],
            "camera": ["tire uma foto", "foto", "webcam", "capturar minha imagem", "bata uma foto"],
            "whatsapp": ["mandar mensagem", "enviar mensagem", "whatsapp", "jimi mandar"]
        }

    def _match_intent(self, text: str):
        # Busca por correspondência de palavras-chave nas intenções mapeadas
        for intent, keywords in self.intents.items():
            if any(keyword in text for keyword in keywords):
                return intent
        return "unknown"

    def plan(self, user_input: str):
        text = user_input.lower().strip()
        intent = self._match_intent(text)
        
        logger.info(f"[PLANNER] Fluxo de intenção identificado: {intent}")

        # 1. Navegação Web
        if intent == "web_navigation":
            return {"type": "open_url", "value": self._extract_url(text)}
        
        # 2. Comandos de Sistema Operacional
        if intent == "system":
            return {"type": "system", "value": self._map_system_action(text)}
        
        # 3. Perfis de Automação Macro
        if intent == "automation":
            return {"type": "automation", "value": "work_mode"}

        # 4. Ciclo de Auto-Evolução (Modificação de código fonte)
        if intent == "self_evolution":
            target_file, details = self._extract_evolution_details(user_input)
            return {
                "type": "evolve",
                "value": target_file,
                "meta": {
                    "target_file": target_file,
                    "details": details
                }
            }

        # 5. Próximo Módulo: Captura de Câmera Local
        if intent == "camera":
            return {"type": "camera", "value": "take_photo"}

        # 6. Próximo Módulo: Automação do WhatsApp (Voz para texto)
        if intent == "whatsapp":
            return {"type": "whatsapp", "value": user_input}

        # Se não corresponder a nenhuma automação física, repassa o texto bruto para o Brain responder via Chatbot
        return {"type": "chat", "value": user_input}

    def _extract_url(self, text):
        if "youtube" in text: return "https://youtube.com"
        if "google" in text: return "https://google.com"
        
        # Tenta pescar URLs explícitas digitadas no chat
        url_match = re.search(r"https?://[^\s]+", text)
        if url_match:
            return url_match.group(0)
        return None

    def _map_system_action(self, text):
        if "desligar" in text: return "shutdown /s /t 0"
        if "reiniciar" in text: return "shutdown /r /t 0"
        return None

    def _extract_evolution_details(self, text):
        """
        Analisa a string e isola o caminho do script (.py) e os detalhes da alteração.
        Exemplo: "Jimi, melhore o arquivo voice/audio_ai.py adicionando suporte a logs extras"
        Retorna: ("voice/audio_ai.py", "adicionando suporte a logs extras")
        """
        # Captura extensões .py com caminhos (ex: core/brain.py, services/camera_service.py)
        file_match = re.search(r"([\w_/-]+\.py)", text, re.IGNORECASE)
        target_file = file_match.group(1) if file_match else None
        
        details = text
        if target_file:
            # Divide o texto no nome do arquivo para capturar tudo o que vem depois como instrução
            parts = text.split(target_file, 1)
            if len(parts) > 1 and parts[1].strip():
                # Limpa conectivos comuns como "para", "com", "removendo" do início da frase
                details = re.sub(r"^(para|com|que|adicionando)\s+", "", parts[1].strip(), flags=re.IGNORECASE)
        
        return target_file, details

# Instância global unificada
planner = Planner()