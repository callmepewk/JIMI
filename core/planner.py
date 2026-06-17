import logging

class Planner:
    def __init__(self):
        # Mapeamento de intenções (Intenção -> Ação/Função)
        self.intents = {
            "web_navigation": ["abrir", "navegar", "acessar"],
            "app_control": ["executar", "abrir aplicativo"],
            "system": ["desligar", "reiniciar", "suspender"],
            "automation": ["modo trabalho", "modo foco", "configurar ambiente"]
        }

    def _match_intent(self, text: str):
        # Busca por similaridade de intenção
        for intent, keywords in self.intents.items():
            if any(keyword in text for keyword in keywords):
                return intent
        return "unknown"

    def plan(self, user_input: str):
        text = user_input.lower().strip()
        intent = self._match_intent(text)
        
        # Orquestração da ação baseada na intenção
        if intent == "web_navigation":
            return {"type": "open_url", "value": self._extract_url(text)}
        
        if intent == "system":
            return {"type": "system", "value": self._map_system_action(text)}
        
        if intent == "automation":
            return {"type": "automation", "value": "work_mode"}

        return {"type": "chat", "value": "Não entendi a tarefa, poderia repetir?"}

    def _extract_url(self, text):
        # Lógica inteligente para extrair sites de frases naturais
        if "youtube" in text: return "https://youtube.com"
        if "google" in text: return "https://google.com"
        return None

    def _map_system_action(self, text):
        if "desligar" in text: return "shutdown /s /t 0"
        return None

# Instância global
planner = Planner()