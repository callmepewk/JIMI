import pyautogui
import subprocess
import time
import webbrowser
import os
import requests
import datetime
import logging

# Configuração de Logs para auditoria do que o JIMI está fazendo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class JimiAutomation:
    def __init__(self):
        self.pyautogui = pyautogui
        self.pyautogui.PAUSE = 0.2
        self.context = {"waiting_spotify": False}
        logging.info("JIMI Automation System Initialized.")

    # --- Comandos de Sistema Seguros ---
    def safe_execute(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Erro ao executar {func.__name__}: {e}")
            return f"Desculpe Sr. Pedro, não consegui executar isso: {str(e)}"

    def open_app(self, app_path_or_name):
        return self.safe_execute(subprocess.Popen, app_path_or_name)

    # --- Automação Robusta ---
    def perform_system_action(self, action):
        actions = {
            "shutdown": lambda: os.system("shutdown /s /t 1"),
            "restart": lambda: os.system("shutdown /r /t 1"),
            "mute": lambda: self.pyautogui.press("volumemute")
        }
        if action in actions:
            return self.safe_execute(actions[action])
        return "Comando de sistema não reconhecido."

    # --- Módulo de Pesquisa ---
    def smart_search(self, query):
        """Busca refinada com fallback"""
        try:
            # Integração futura com o cérebro (LLM) aqui
            response = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json", timeout=5)
            data = response.json()
            return data.get("Abstract") or "Não encontrei informações precisas, Sr. Pedro."
        except Exception:
            return "Minha conexão com a rede de dados falhou."

    # --- O Coração das Intenções ---
    def process_command(self, text):
        text = text.lower()
        
        # Estrutura modular de intents
        if "abrir" in text:
            return self._handle_open_intent(text)
        elif "pesquisar" in text:
            return self.smart_search(text.replace("pesquisar", ""))
        elif "desligar" in text:
            return self.perform_system_action("shutdown")
        
        return "Comando não mapeado. Gostaria que eu pesquisasse sobre isso?"

    def _handle_open_intent(self, text):
        mapping = {
            "spotify": "spotify",
            "vscode": "code",
            "whatsapp": "https://web.whatsapp.com"
        }
        for key, cmd in mapping.items():
            if key in text:
                if cmd.startswith("http"):
                    webbrowser.open(cmd)
                else:
                    self.open_app(cmd)
                return f"Abrindo {key} para o senhor, Sr. Pedro."
        return "Não sei qual aplicativo deseja abrir."

# Instância única para ser usada por todo o sistema
jimi_core = JimiAutomation()